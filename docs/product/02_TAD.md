# Technical Architecture Document (TAD)

**Project:** ConceptKart ETL Pipeline v2.0
**Status:** Approved

## 1. System Context
The system is divided into an Agentic Control Plane (`.agents/`) that governs rules, and an Application Plane (`src/`) that performs the data ingestion.

## 2. High-Level Architecture
- **Control Node:** `main.py` orchestrated by `APScheduler`.
- **Extraction:** `extractor.py` implementing a 3-tier strategy.
- **Validation:** Pydantic `ScrapedProduct` model.
- **Data Persistence:** Supabase PostgreSQL for remote cloud state, and local DuckDB/Parquet for telemetry and DLQ state.

## 3. Data Flow
1. Scheduler triggers extraction for active domains.
2. HTTP/Browser/LLM tier returns raw text/JSON.
3. Pydantic validates the schema.
4. If valid, UPSERT to Supabase.
5. If invalid/failed, push to Parquet Dead-Letter Queue (DLQ).

## 4. Technology Stack
- Python 3.11+
- curl-cffi, Crawl4AI
- Groq/OpenRouter/HuggingFace APIs
- DuckDB, PyArrow
- Supabase Python SDK
