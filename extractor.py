"""
Extraction Cascade Orchestrator.

Routes extraction requests through the 3-tier cascade:
  Tier 1 (curl-cffi + BS4) → Tier 2 (Crawl4AI browser) → Tier 3 (LLM AI)

Each tier falls through to the next on failure. Circuit breakers
prevent repeatedly calling tiers that are consistently failing
for a specific domain.

This module replaces the original monolithic scrape_conceptkart() function
with a site-agnostic, cascading extraction engine.
"""

import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from src.models import ScrapedProduct, SiteConfig, PipelineMetric
from src.extractors.tier1_http import Tier1HttpExtractor
from src.extractors.tier2_browser import Tier2BrowserExtractor
from src.extractors.tier3_llm import Tier3LlmExtractor
from src.sites.registry import get_site_config, cache_site_config
from src.stealth.fingerprints import get_random_delay
from src.observability.logger import log_error
from src.observability.metrics import record_metric


# Singleton extractor instances (circuit breaker state persists across calls)
_tier1 = Tier1HttpExtractor()
_tier2 = Tier2BrowserExtractor()
_tier3 = Tier3LlmExtractor()


def extract_product(url: str, tracked_product_id: Optional[int] = None) -> Optional[ScrapedProduct]:
    """Run the 3-tier extraction cascade for a product URL.
    
    Args:
        url: The product page URL to scrape.
        tracked_product_id: Optional ID for telemetry correlation.
        
    Returns:
        ScrapedProduct on success, None on total failure.
    """
    domain = urlparse(url).netloc.replace("www.", "")
    site_config = get_site_config(domain)
    start_ms = time.monotonic_ns()

    print(f"\n  Extracting: {url}")
    print(f"  Domain: {domain} | JS required: {site_config.requires_js} | LLM required: {site_config.requires_llm}")

    # Determine which tiers to attempt
    tiers = _build_tier_sequence(site_config)

    result: Optional[ScrapedProduct] = None
    last_error: Optional[str] = None

    for tier_name, extractor in tiers:
        try:
            print(f"  Attempting {tier_name}...")
            result = extractor.extract(url, site_config=site_config)

            if result:
                print(f"  [SUCCESS] {tier_name} succeeded: {result.product_name} @ Rs.{result.price_current}")

                # If Tier 3 succeeded on an unknown site, cache the config
                if tier_name == "tier3_llm" and domain not in _get_known_domains():
                    cache_site_config(domain, SiteConfig(requires_llm=True))

                # Record success metric
                _record(domain, tracked_product_id, tier_name,
                        int((time.monotonic_ns() - start_ms) / 1_000_000), True)
                return result
            else:
                print(f"  [FAIL] {tier_name} returned None.")
                last_error = f"{tier_name}_returned_none"

        except Exception as e:
            print(f"  [FAIL] {tier_name} raised: {e}")
            last_error = type(e).__name__
            log_error(e, component=f"extractor.{tier_name}", domain=domain, tier=tier_name)

    # All tiers failed
    total_ms = int((time.monotonic_ns() - start_ms) / 1_000_000)
    print(f"  [FATAL] ALL TIERS FAILED for {url} (total: {total_ms}ms)")
    _record(domain, tracked_product_id, "all_failed", total_ms, False, last_error)
    return None


def _build_tier_sequence(site_config: SiteConfig) -> list[tuple[str, object]]:
    """Build the tier execution sequence based on site config.
    
    Some sites are known to require JS (skip Tier 1) or LLM (skip Tier 1+2).
    """
    tiers = []

    if not site_config.requires_js and not site_config.requires_llm:
        tiers.append(("tier1_http", _tier1))

    if not site_config.requires_llm:
        tiers.append(("tier2_browser", _tier2))

    tiers.append(("tier3_llm", _tier3))

    return tiers


def _get_known_domains() -> set[str]:
    """Get the set of domains with hardcoded configs."""
    from src.sites.registry import SITE_REGISTRY
    return set(SITE_REGISTRY.keys())


def _record(
    domain: str,
    product_id: Optional[int],
    tier: str,
    latency_ms: int,
    success: bool,
    error_type: Optional[str] = None,
) -> None:
    """Record a pipeline metric to the DuckDB telemetry plane."""
    try:
        record_metric(PipelineMetric(
            timestamp_utc=datetime.now(timezone.utc),
            domain=domain,
            tracked_product_id=product_id,
            tier_used=tier,
            latency_ms=latency_ms,
            success=success,
            error_type=error_type,
        ))
    except Exception:
        pass  # Telemetry must never crash the pipeline


# === BACKWARDS COMPATIBILITY ===
# The original codebase calls `scrape_conceptkart(url)` from main.py.
# This shim preserves that interface while routing through the new cascade.

def scrape_conceptkart(url: str = None) -> dict:
    """Legacy interface — routes through the new extraction cascade.
    
    Returns a plain dict (not Pydantic) for backwards compatibility
    with the existing load_data.py and price_check.py modules.
    """
    if not url:
        url = "https://conceptkart.com/products/shanling-eh1"

    result = extract_product(url)

    if result:
        return {
            "product_name": result.product_name,
            "vendor_name": result.vendor_name,
            "vendor_url": result.vendor_url,
            "price_current": result.price_current,
            "scraped_at_utc": result.scraped_at_utc.isoformat(),
        }

    # Total cascade failure — raise to maintain existing error handling behavior
    raise ValueError(f"FATAL: All extraction tiers failed for {url}")