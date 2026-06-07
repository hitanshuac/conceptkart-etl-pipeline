# Test Plan: Core ETL Capabilities

**Epic Source:** Epic 1 & 2 (Validation and Database Idempotency)
**Date:** 2026-06-07

## 1. Unit Tests

### Test: `test_validation_valid_payload`
- **Type:** Unit
- **Target:** `price_check.validate_price_payload`
- **Setup:** None.
- **Action:** Pass a correctly structured payload dictionary to the validator.
- **Assertion:** Expect `is_valid` to be `True`.

### Test: `test_validation_invalid_price`
- **Type:** Unit
- **Target:** `price_check.validate_price_payload`
- **Setup:** None.
- **Action:** Pass a payload with `price_current: 0` or negative.
- **Assertion:** Expect `is_valid` to be `False`.

## 2. Integration Tests

### Test: `test_dlq_store_and_forward`
- **Type:** Integration
- **Target:** `load_data.load_to_database`
- **Setup:** Mock the `supabase.table().upsert().execute()` call to raise an `Exception` simulating a network outage.
- **Action:** Attempt to load a valid payload into the database.
- **Assertion:** Ensure the payload is written to the Parquet Dead-Letter Queue instead of failing silently.

### Test: `test_db_idempotent_upsert`
- **Type:** Integration
- **Target:** `load_data.load_to_database`
- **Setup:** Mock the `supabase.table().upsert()` to succeed.
- **Action:** Load identical payload twice.
- **Assertion:** Ensure `upsert` is called instead of `insert` to prevent primary key collisions.
