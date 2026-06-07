# Rule 03: Quarantine DLQ

**Mandate:** Robust error handling and data validation are strictly enforced.

1. **Dead-Letter Queue (DLQ):** Any validation failures encountered via Pydantic parsing must NOT crash the main event loop or ingestion process.
2. **Quarantine Routing:** Malformed records must be explicitly routed to `data/quarantine_log.parquet`.
3. **Observability:** This quarantine mechanism ensures that all data issues are isolated and logged for later review without halting the automated pipeline.
