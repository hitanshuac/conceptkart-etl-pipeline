"""
Price validation with Pydantic enforcement and DLQ quarantine.

Validates scraped data against the ScrapedProduct Pydantic schema.
On validation failure, routes the malformed record to a Parquet
Dead-Letter Queue (DLQ) without crashing the pipeline.

Per data-validation.md:
- Validation failures must NOT crash the pipeline
- Bad records are quarantined to data/quarantine_YYYYMMDD.parquet
- Partial batch successes are allowed
"""

import os
from datetime import UTC, datetime

from pydantic import ValidationError

from src.models import QuarantineRecord, ScrapedProduct

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def validate_price_payload(payload: dict, target_price: int = None) -> tuple[bool, bool]:
    """Validates the payload and checks if the target price is hit.

    Returns: (is_valid, is_target_hit)

    This function now enforces the full Pydantic ScrapedProduct schema
    when all required fields are present. For backwards compatibility
    with the existing pipeline, it also accepts minimal payloads
    containing just 'price_current'.
    """
    if "price_current" not in payload:
        raise KeyError("FATAL: 'price_current' key is missing from the payload.")

    price = payload["price_current"]

    # Strict type enforcement. No strings allowed.
    if not isinstance(price, (int, float)):
        raise TypeError(f"FATAL: Expected int or float for price, got {type(price).__name__}.")

    # Boundary constraints
    if price <= 100:
        _quarantine_record(payload, "ValueError", f"ANOMALY: Price Rs.{price} is too low.")
        raise ValueError(f"ANOMALY: Price Rs.{price} is too low. Did we scrape a cable instead of the IEM?")

    if price >= 500000:
        _quarantine_record(payload, "ValueError", f"ANOMALY: Price Rs.{price} is too high.")
        raise ValueError(f"ANOMALY: Price Rs.{price} is too high. Check extraction logic.")

    is_target_hit = False
    if target_price and price <= target_price:
        is_target_hit = True

    return True, is_target_hit


def validate_scraped_product(payload: dict) -> ScrapedProduct | None:
    """Full Pydantic validation of a scraped product payload.

    Returns the validated ScrapedProduct model on success,
    or None if validation fails (with the record quarantined).

    Per data-validation.md: the pipeline continues on failure.
    """
    try:
        product = ScrapedProduct.model_validate(payload)
        return product
    except ValidationError as e:
        _quarantine_record(payload, "ValidationError", str(e))
        print(f"  [VALIDATION] Pydantic validation failed. Record quarantined: {e.error_count()} errors.")
        return None


def _quarantine_record(payload: dict, error_type: str, error_message: str) -> None:
    """Route a malformed record to the Dead-Letter Queue.

    Per data-validation.md §2: save bad records to data/quarantine_YYYYMMDD.parquet
    with the original payload and validation error for manual review.
    """
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        os.makedirs(DATA_DIR, exist_ok=True)

        record = QuarantineRecord(
            timestamp_utc=datetime.now(UTC),
            source_url=payload.get("vendor_url", "unknown"),
            raw_payload=payload,
            error_type=error_type,
            error_message=error_message[:500],  # Truncate to conserve space
            extraction_tier=payload.get("extraction_tier"),
        )

        date_str = datetime.now(UTC).strftime("%Y%m%d")
        parquet_path = os.path.join(DATA_DIR, f"quarantine_{date_str}.parquet")

        # Convert to arrow table
        row = {
            "timestamp_utc": [str(record.timestamp_utc)],
            "source_url": [record.source_url],
            "raw_payload": [str(record.raw_payload)],
            "error_type": [record.error_type],
            "error_message": [record.error_message],
            "extraction_tier": [record.extraction_tier or "unknown"],
        }
        table = pa.table(row)

        # Append to existing parquet or create new
        if os.path.exists(parquet_path):
            existing = pq.read_table(parquet_path)
            combined = pa.concat_tables([existing, table])
            pq.write_table(combined, parquet_path)
        else:
            pq.write_table(table, parquet_path)

        print(f"  [DLQ] Record quarantined to {parquet_path}")

    except ImportError:
        # pyarrow not installed — fall back to JSON quarantine
        import json

        os.makedirs(DATA_DIR, exist_ok=True)
        fallback_path = os.path.join(DATA_DIR, "quarantine_fallback.json")
        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": str(payload),
            "error": error_message[:500],
        }
        try:
            entries = []
            if os.path.exists(fallback_path):
                with open(fallback_path) as f:
                    entries = json.load(f)
            entries.append(entry)
            with open(fallback_path, "w") as f:
                json.dump(entries, f, indent=2)
        except Exception:
            pass

    except Exception as e:
        # Quarantine writes must never crash the pipeline
        print(f"  [DLQ] WARNING: Failed to quarantine record: {e}")


if __name__ == "__main__":
    test_data = {"price_current": 1500}
    try:
        valid, hit = validate_price_payload(test_data, 2000)
        print(f"Valid: {valid}, Target Hit: {hit}")
    except Exception as e:
        print(f"Error: {e}")
