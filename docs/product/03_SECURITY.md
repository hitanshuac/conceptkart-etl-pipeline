# Security & Governance Document

**Project:** ConceptKart ETL Pipeline v2.0
**Status:** Approved

## 1. Governance Rules (Agentic)
- **Rule 00**: Agents must never delete legacy code unless authorized.
- **Rule 01**: All new config must comply with 12-Factor principles (Environment Variables).

## 2. Secrets Management
- Keys (`SUPABASE_ANON_KEY`, `GROQ_API_KEY`, etc.) are injected strictly via `.env` files.
- `.env` files are in `.gitignore` and never committed.
- The pipeline uses a `dashboard/.env` fallback configuration to maintain credential parity with the React UI.

## 3. Data Integrity
- Pydantic models act as a hard boundary. If scraped text includes injected scripts or bad data formats, Pydantic raises a ValidationError, quarantining the payload to the DLQ instead of polluting the cloud SQL database.
