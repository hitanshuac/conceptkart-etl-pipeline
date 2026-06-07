"""
Tier 2: JavaScript rendering via Crawl4AI + Playwright Stealth.

Triggered when Tier 1 fails (403, empty price, JS-rendered content).
Uses Crawl4AI's async browser with stealth patches to render JavaScript-heavy
sites (React/Angular SPAs) and extract structured data via Pydantic schemas.

Cost: $0 (open source, self-hosted). Latency: ~2-5s.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from src.extractors.base import BaseExtractor
from src.models import ScrapedProduct, SiteConfig

# Crawl4AI is optional — Tier 2 gracefully degrades if not installed
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False


class Tier2BrowserExtractor(BaseExtractor):
    """Browser-based extraction for JavaScript-heavy sites.
    
    Uses Crawl4AI which internally manages Playwright with stealth patches.
    Extraction strategies:
    1. CSS-based extraction (fast, if selectors are known)
    2. Crawl4AI's built-in content analysis (markdown conversion + parsing)
    """

    tier_name = "tier2_browser"

    def extract(
        self,
        url: str,
        site_config: Optional[SiteConfig] = None,
        **kwargs,
    ) -> Optional[ScrapedProduct]:
        if not HAS_CRAWL4AI:
            print("  [Tier2] crawl4ai not installed. Skipping browser tier.")
            return None

        domain = urlparse(url).netloc.replace("www.", "")

        if not self.can_attempt(domain):
            print(f"  [Tier2] Circuit open for {domain}, skipping.")
            return None

        # Run the async extraction in a sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in an async context, create a new loop
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run, self._async_extract(url, domain, site_config)
                    ).result(timeout=30)
                return result
            else:
                return asyncio.run(self._async_extract(url, domain, site_config))
        except Exception as e:
            print(f"  [Tier2] Event loop error: {e}")
            self.circuit_breaker.record_failure(domain)
            return None

    async def _async_extract(
        self,
        url: str,
        domain: str,
        site_config: Optional[SiteConfig],
    ) -> Optional[ScrapedProduct]:
        """Core async extraction using Crawl4AI."""
        start_ms = time.monotonic_ns()

        try:
            config = CrawlerRunConfig(
                wait_until="networkidle",
                page_timeout=20000,
                verbose=False,
            )

            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=config)

                if not result.success:
                    print(f"  [Tier2] Crawl failed for {url}: {result.error_message}")
                    self.circuit_breaker.record_failure(domain)
                    return None

                # Try to extract product data from the crawled markdown
                product_name, price_current = self._parse_crawl_result(result, site_config)

                if price_current == 0 or not product_name:
                    print("  [Tier2] Could not extract price/name from rendered page.")
                    self.circuit_breaker.record_failure(domain)
                    return None

                latency_ms = int((time.monotonic_ns() - start_ms) / 1_000_000)
                self.circuit_breaker.record_success(domain)

                return ScrapedProduct(
                    product_name=product_name,
                    vendor_name=domain,
                    vendor_url=url,
                    price_current=price_current,
                    scraped_at_utc=datetime.now(timezone.utc),
                    extraction_tier=self.tier_name,
                    extraction_latency_ms=latency_ms,
                )

        except Exception as e:
            print(f"  [Tier2] Exception during browser extraction: {e}")
            self.circuit_breaker.record_failure(domain)
            return None

    def _parse_crawl_result(self, result, site_config: Optional[SiteConfig]) -> tuple:
        """Parse the Crawl4AI result to extract product name and price.
        
        Uses the HTML from the rendered page and applies the same
        parsing strategies as Tier 1 (OG meta, JSON-LD, CSS selectors)
        but on the fully-rendered DOM.
        """
        import json
        import re
        from bs4 import BeautifulSoup

        html = result.html if hasattr(result, 'html') else ""
        if not html:
            return None, 0

        soup = BeautifulSoup(html, "html.parser")
        product_name = None
        price_current = 0

        # Strategy 1: Open Graph meta
        title_meta = soup.find("meta", property="og:title")
        price_meta = soup.find("meta", property="og:price:amount")
        if title_meta and title_meta.get("content"):
            product_name = title_meta["content"]
        if price_meta and price_meta.get("content"):
            try:
                price_current = int(float(price_meta["content"]))
            except (ValueError, TypeError):
                pass

        # Strategy 2: JSON-LD
        if price_current == 0:
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string)
                    items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                    for item in items:
                        if item.get("@type") == "Product":
                            offers = item.get("offers", {})
                            if isinstance(offers, list):
                                offers = offers[0] if offers else {}
                            price_str = offers.get("price", "0")
                            price_current = int(float(price_str))
                            product_name = item.get("name", product_name)
                            if price_current > 0:
                                break
                except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                    continue

        # Strategy 3: Site-specific CSS selectors
        if price_current == 0 and site_config and site_config.selectors:
            price_sel = site_config.selectors.get("price")
            name_sel = site_config.selectors.get("name")
            if price_sel:
                elem = soup.select_one(price_sel)
                if elem:
                    raw = elem.get("content", elem.text)
                    price_current = self._parse_price(raw)
            if name_sel and not product_name:
                elem = soup.select_one(name_sel)
                if elem:
                    product_name = elem.get("content", elem.text).strip()

        # Strategy 4: Generic CSS patterns
        if price_current == 0:
            price_patterns = re.compile(
                r"price-item--regular|price__regular|product-price|"
                r"current-price|sale-price|offer-price"
            )
            elem = soup.find(class_=price_patterns)
            if elem:
                price_current = self._parse_price(elem.text)

        # Fallback: get product name from <title>
        if not product_name:
            title_tag = soup.find("title")
            if title_tag:
                product_name = title_tag.text.strip().split("|")[0].split("–")[0].strip()

        return product_name, price_current

    @staticmethod
    def _parse_price(raw: str) -> int:
        """Clean and parse a price string into an integer."""
        if not raw:
            return 0
        cleaned = raw.strip().replace("Rs.", "").replace("₹", "")
        cleaned = cleaned.replace(",", "").replace(" ", "")
        try:
            return int(float(cleaned))
        except (ValueError, TypeError):
            return 0
