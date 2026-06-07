# Project Context

## Purpose

ConceptKart ETL Pipeline is a high-availability, site-agnostic pricing engine. Its primary workflow is:
- Track e-commerce pricing continuously via `main.py` and `daemon.py`.
- Ensure zero-cost scalability by leveraging free LLM tiers and open-source tooling.
- Provide highly reliable data extraction through a dynamic 3-Tier Cascade that falls back to AI Self-Healing when structural parsing fails.

## Tech Stack

- **Language:** Python 3.11+
- **LLM Providers:** OpenAI-compatible endpoints by default (Groq, OpenRouter, HuggingFace support natively embedded).
- **Data Validation:** Pydantic `ScrapedProduct` model enforces strict bounds to prevent injection of bad data.
- **Cloud State:** Supabase (PostgreSQL) handles all `tracked_products` and `raw_daily_prices`.
- **Local Telemetry:** DuckDB powers a fast, non-blocking metrics store for analyzing circuit-breaker state and latency.
- **Extraction Tools:** `curl-cffi` (Tier 1), `Crawl4AI` (Tier 2).

## Project Conventions

### Code Style
- Explicit Pydantic data contracts over implicit dictionaries.
- 12-Factor App rules are strictly enforced (all config via environment variables, stateless execution).
- SQL Idempotency: All data inserts must use `UPSERT` or `INSERT OR REPLACE` to prevent duplication during network retries.

### Architecture Patterns
- **Split-Plane Environment:** The Agentic Control Plane (`.agents/`) dictates the rules, and the Application Plane (`src/`) executes them mechanically.
- **Circuit Breaker:** Per-domain failure thresholds prevent the pipeline from burning resources on blocked sites.
- **Store-and-Forward:** A Parquet-backed Dead-Letter Queue (DLQ) ensures no data is lost during cloud database outages.

### Testing Strategy
- The environment relies on SRE validation via DuckDB metrics and Parquet DLQ checks.
- Changes to core parsing logic must pass the Pydantic bounds test.

### Git Workflow
- All pipeline adjustments must be synced with documentation using the `master-sync.md` workflow.
- Commits follow production changelog standards (Semantic Release / Changesets).

## Security Boundaries
- Secrets must never be committed. `.env` loading is strictly enforced via `os.environ`.
- The Pydantic boundaries are absolute. A price of Rs. 0 or Rs. 100,000,000 will be instantly quarantined to the DLQ.
