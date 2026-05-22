# Project Error & Resolution Log

This document tracks historical errors encountered in the ETL pipeline and dashboard, their root causes, and how they were resolved to prevent repetition.

## Timestamp: 2026-05-22
### 1. GitHub Actions Cache Action Error
- **Error**: `No file ... matched to [**/requirements.txt or **/pyproject.toml]` in the `run-etl` workflow.
- **Cause**: The `actions/setup-python@v4` action with `cache: 'pip'` requires a dependency file to hash for the cache key, but the project had no `requirements.txt`.
- **Resolution**: Created `requirements.txt` containing `beautifulsoup4` and `requests`. Updated the workflow's install step to run `pip install -r requirements.txt`.
- **Status**: FIXED & RETAINED.

### 2. Node.js 20 Deprecation Warnings
- **Error**: Warning that `actions/checkout@v4` and `setup-python@v4` will be forced to Node 24 by June 2026.
- **Cause**: GitHub Actions deprecating Node 20 runner environments.
- **Resolution**: Injected `env: FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` into `scraper.yml` to opt into Node 24 early and silence the warnings.
- **Status**: FIXED & RETAINED.

### 3. Dashboard Blank Screen (Initialization Crash)
- **Error**: The React dashboard showed a completely white, blank screen on localhost.
- **Cause**: `supabaseClient.js` was trying to initialize `createClient()` with an empty string when the `.env` file was missing. This caused a synchronous `TypeError` that crashed the React app before it could render anything.
- **Resolution**: Refactored `supabaseClient.js` to conditionally initialize the client. If variables are missing, it exports `null`. Added safety checks in `App.jsx` to render a helpful "Missing Configuration" banner instead of crashing.
- **Status**: FIXED & RETAINED.

### 4. Malformed Supabase URL Crash
- **Error**: Dashboard crashed with `TypeError: URL constructor: vlunitbvwpskrzvokgyw is not a valid URL`.
- **Cause**: The user provided just the raw Project ID (`vlunitbvwpskrzvokgyw`) in the `.env` file instead of the fully qualified `https://...` URL.
- **Resolution**: Updated `supabaseClient.js` to intelligently auto-format the URL. If the provided URL lacks `http`, it now automatically wraps it as `https://{URL}.supabase.co`.
- **Status**: FIXED & RETAINED.

### 5. Missing Supabase Tables (Migration Gap)
- **Error**: `Could not find the table 'public.tracked_products' in the schema cache.`
- **Cause**: The React dashboard connected to Supabase successfully, but the Python ETL was still writing to a local SQLite database (`prices.db`), so the cloud tables didn't exist.
- **Resolution**: 
  - Provided a unified SQL script to the user to create `tracked_products`, `raw_daily_prices`, and a `dashboard_view` in Supabase.
  - Migrated the Python backend (`load_data.py`, `main.py`, `db_setup.py`) to use the `supabase` Python SDK instead of SQLite.
  - Added `python-dotenv` so the Python script can share the dashboard's `.env` file seamlessly.
- **Status**: FIXED & RETAINED. Local SQLite is completely deprecated.

### 6. RLS Insert Error & API Provider Pivot
- **Error**: Dashboard failed to add a product with `new row violates row-level security policy for table "tracked_products"`. Additionally, user hit Gemini API rate limits.
- **Cause**: Supabase blocks UI inserts by default. Gemini free tier is highly restrictive for automated scraping.
- **Resolution**: 
  - Instructed user to run the `Allow public insert` RLS policy SQL snippet in Supabase.
  - Ripped out `google-genai` and replaced it with the official `openai` Python SDK.
  - Reconfigured `extractor.py` to seamlessly route requests through OpenRouter or Groq based on which API key the user provides, defaulting to free/cheap Llama 3 models using strict JSON mode.
- **Status**: FIXED & RETAINED. Architecture is now provider-agnostic.
