"""
Pydantic data contracts for the Dynamic Pricing Tracker.
Single source of truth for all data models across the pipeline.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SiteConfig(BaseModel):
    """Per-site extraction configuration overrides.

    Allows the system to optimize extraction strategy per domain
    without modifying application code.
    """

    selectors: dict | None = None
    requires_js: bool = False
    requires_llm: bool = False
    custom_headers: dict | None = None
    rate_limit_seconds: int = Field(default=5, ge=1, le=300)


class ScrapedProduct(BaseModel):
    """Validated output from the extraction cascade.

    All 3 extraction tiers must produce data conforming to this schema.
    Pydantic validation failures are routed to the DLQ quarantine.
    """

    product_name: str = Field(min_length=1, max_length=500)
    vendor_name: str = Field(min_length=1, max_length=200)
    vendor_url: str
    price_current: int = Field(gt=100, lt=500000)
    currency: str = Field(default="INR", max_length=10)
    scraped_at_utc: datetime
    extraction_tier: Literal["tier1_http", "tier2_browser", "tier3_llm"]
    extraction_latency_ms: int = Field(ge=0)


class TrackedProduct(BaseModel):
    """A product being actively monitored by the pricing tracker."""

    id: int
    url: str
    target_price: int = Field(gt=0)
    is_active: bool = True
    site_config: SiteConfig | None = None


class QuarantineRecord(BaseModel):
    """A malformed record routed to the Dead-Letter Queue.

    Per data-validation.md: validation failures must never crash the pipeline.
    Bad records are serialized here and written to data/quarantine_*.parquet.
    """

    timestamp_utc: datetime
    source_url: str
    raw_payload: dict
    error_type: str
    error_message: str
    extraction_tier: str | None = None


class PipelineMetric(BaseModel):
    """Telemetry record written to the DuckDB metrics plane.

    Per context_compaction.md §6: every request records compaction
    and extraction metrics for SRE observability.
    """

    timestamp_utc: datetime
    domain: str
    tracked_product_id: int | None = None
    tier_used: str
    latency_ms: int
    success: bool
    error_type: str | None = None
    tokens_used: int = 0
    proxy_used: bool = False
    http_status: int | None = None
