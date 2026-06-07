"""
Per-site extraction configuration registry.

This is what makes the tracker work for "any website". Known sites
have optimized selector configs. Unknown sites fall through the
extraction cascade and auto-generate configs from LLM results.

Registry lives in code (version-controlled) for reliability.
"""

from src.models import SiteConfig


# Known site configurations with optimized CSS selectors.
# When a product URL matches a domain key here, the extractor
# uses these selectors for faster, more reliable extraction.
SITE_REGISTRY: dict[str, SiteConfig] = {
    # --- Indian E-Commerce ---
    "conceptkart.com": SiteConfig(
        selectors={
            "price": "meta[property='og:price:amount']",
            "name": "meta[property='og:title']",
        },
        requires_js=False,
        rate_limit_seconds=5,
    ),
    "headphonezone.in": SiteConfig(
        selectors={
            "price": ".product-single__price .money",
            "name": "h1.product-single__title",
        },
        requires_js=False,
        rate_limit_seconds=10,
    ),
    "amazon.in": SiteConfig(
        selectors={
            "price": "#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen",
            "name": "#productTitle",
        },
        requires_js=True,
        rate_limit_seconds=15,
    ),
    "flipkart.com": SiteConfig(
        selectors={
            "price": "div._30jeq3",
            "name": "span.VU-ZEz",
        },
        requires_js=True,
        rate_limit_seconds=15,
    ),
    # --- International ---
    "amazon.com": SiteConfig(
        selectors={
            "price": "#priceblock_ourprice, #priceblock_dealprice, .a-price .a-offscreen",
            "name": "#productTitle",
        },
        requires_js=True,
        rate_limit_seconds=15,
    ),
    # --- Generic Shopify sites ---
    # Most Shopify stores share the same meta tag structure.
    # If a site uses Shopify, Tier 1 OG meta extraction usually works.
}

# Runtime cache for auto-generated configs from Tier 3 LLM results.
# These are ephemeral and lost on restart — successful extractions
# should be manually added to SITE_REGISTRY above.
_runtime_cache: dict[str, SiteConfig] = {}


def get_site_config(domain: str) -> SiteConfig:
    """Look up the extraction config for a domain.
    
    Priority:
    1. SITE_REGISTRY (hardcoded, version-controlled)
    2. _runtime_cache (auto-generated from LLM, ephemeral)
    3. Default config (generic extraction, no selectors)
    """
    # Normalize domain
    domain = domain.replace("www.", "").lower()

    if domain in SITE_REGISTRY:
        return SITE_REGISTRY[domain]

    if domain in _runtime_cache:
        return _runtime_cache[domain]

    # Default: try generic extraction (OG meta, JSON-LD)
    return SiteConfig()


def cache_site_config(domain: str, config: SiteConfig) -> None:
    """Cache a runtime-discovered site config.
    
    Called when Tier 3 LLM successfully extracts data from an
    unknown site. The config is cached for the duration of
    the process to speed up subsequent scrapes of the same domain.
    """
    domain = domain.replace("www.", "").lower()
    _runtime_cache[domain] = config
    print(f"[SiteRegistry] Cached runtime config for {domain}")


def list_known_sites() -> list[str]:
    """List all domains with known extraction configs."""
    return sorted(list(SITE_REGISTRY.keys()) + list(_runtime_cache.keys()))
