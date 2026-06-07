"""
Tier 1: Fast HTTP extraction using curl-cffi + BeautifulSoup.

This is the cheapest and fastest tier. It uses curl-cffi to impersonate
a real browser's TLS fingerprint (bypassing basic WAF checks) and
BeautifulSoup to parse structured data from meta tags, JSON-LD, and
CSS selectors.

Cost: $0. Latency: ~200-500ms.
"""

import json
import re
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from src.extractors.base import BaseExtractor
from src.models import ScrapedProduct, SiteConfig
from src.stealth.fingerprints import get_stealth_headers

# curl-cffi is the gold standard for TLS fingerprint impersonation.
# Falls back to requests if curl-cffi is not installed.
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    import requests as cffi_requests
    HAS_CURL_CFFI = False


class Tier1HttpExtractor(BaseExtractor):
    """Fast HTTP extraction with TLS impersonation.
    
    Extraction priority:
    1. Open Graph meta tags (og:price:amount, og:title)
    2. JSON-LD structured data (@type: Product)
    3. Site-specific CSS selectors from SiteConfig
    4. Generic price-class CSS fallback
    """

    tier_name = "tier1_http"

    def extract(
        self,
        url: str,
        site_config: Optional[SiteConfig] = None,
        **kwargs,
    ) -> Optional[ScrapedProduct]:
        domain = urlparse(url).netloc.replace("www.", "")

        if not self.can_attempt(domain):
            print(f"  [Tier1] Circuit open for {domain}, skipping.")
            return None

        start_ms = time.monotonic_ns()

        try:
            headers = get_stealth_headers()
            if site_config and site_config.custom_headers:
                headers.update(site_config.custom_headers)

            # curl-cffi impersonates Chrome's TLS fingerprint
            if HAS_CURL_CFFI:
                response = cffi_requests.get(
                    url, headers=headers, timeout=15, impersonate="chrome"
                )
            else:
                response = cffi_requests.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                print(f"  [Tier1] HTTP {response.status_code} for {url}")
                self.circuit_breaker.record_failure(domain)
                return None

            # Detect homepage redirects (product removed)
            parsed_response = urlparse(str(response.url))
            if parsed_response.path in ("/", "") and urlparse(url).path not in ("/", ""):
                print("  [Tier1] Redirected to homepage — product likely removed.")
                self.circuit_breaker.record_failure(domain)
                return None

            soup = BeautifulSoup(response.text, "html.parser")
            product_name, price_current = None, 0

            # Strategy 1: Open Graph meta tags
            product_name, price_current = self._extract_opengraph(soup)

            # Strategy 2: JSON-LD structured data
            if price_current == 0:
                product_name, price_current = self._extract_jsonld(
                    soup, product_name
                )

            # Strategy 3: Site-specific CSS selectors
            if price_current == 0 and site_config and site_config.selectors:
                product_name, price_current = self._extract_selectors(
                    soup, site_config.selectors, product_name
                )

            # Strategy 4: Generic CSS fallback
            if price_current == 0:
                price_current = self._extract_generic_css(soup)

            if price_current == 0 or not product_name:
                print(f"  [Tier1] Could not extract price/name from {url}")
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
            print(f"  [Tier1] Exception: {e}")
            self.circuit_breaker.record_failure(domain)
            return None

    def _extract_opengraph(self, soup: BeautifulSoup) -> tuple[Optional[str], int]:
        """Extract from Open Graph meta tags (common in Shopify, WooCommerce)."""
        title_meta = soup.find("meta", property="og:title")
        price_meta = soup.find("meta", property="og:price:amount")

        name = title_meta["content"] if title_meta and title_meta.get("content") else None
        price = 0
        if price_meta and price_meta.get("content"):
            try:
                price = int(float(price_meta["content"]))
            except (ValueError, TypeError):
                pass
        return name, price

    def _extract_jsonld(
        self, soup: BeautifulSoup, fallback_name: Optional[str]
    ) -> tuple[Optional[str], int]:
        """Extract from JSON-LD structured data (@type: Product)."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                # Handle both direct Product and @graph arrays
                items = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                for item in items:
                    if item.get("@type") == "Product":
                        offers = item.get("offers", {})
                        # offers can be a list or dict
                        if isinstance(offers, list):
                            offers = offers[0] if offers else {}
                        price_str = offers.get("price", "0")
                        price = int(float(price_str))
                        name = item.get("name", fallback_name)
                        if price > 0:
                            return name, price
            except (json.JSONDecodeError, TypeError, KeyError, ValueError, IndexError):
                continue
        return fallback_name, 0

    def _extract_selectors(
        self,
        soup: BeautifulSoup,
        selectors: dict,
        fallback_name: Optional[str],
    ) -> tuple[Optional[str], int]:
        """Extract using site-specific CSS selectors from SiteConfig."""
        price = 0
        name = fallback_name

        price_sel = selectors.get("price")
        name_sel = selectors.get("name")

        if price_sel:
            elem = soup.select_one(price_sel)
            if elem:
                # Handle both meta tags and text content
                raw = elem.get("content", elem.text)
                price = self._parse_price(raw)

        if name_sel:
            elem = soup.select_one(name_sel)
            if elem:
                name = elem.get("content", elem.text).strip()

        return name, price

    def _extract_generic_css(self, soup: BeautifulSoup) -> int:
        """Last resort: look for common price CSS class patterns."""
        price_patterns = re.compile(
            r"price-item--regular|price__regular|product-price|"
            r"current-price|sale-price|offer-price"
        )
        elem = soup.find(class_=price_patterns)
        if elem:
            return self._parse_price(elem.text)
        return 0

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
