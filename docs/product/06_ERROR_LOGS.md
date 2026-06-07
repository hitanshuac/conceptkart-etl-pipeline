# Error Logs & Resolutions

**Project:** ConceptKart ETL Pipeline v2.0
**Date:** 2026-06-07

## Overview
This document tracks major production errors, their root causes, and how they were resolved to prevent future regressions.

## Resolved Errors

### 1. Extractor Fallback Failure (conceptkart.com)
**Status:** RESOLVED
**Date:** 2026-06-07
**Error:** `ValueError: FATAL: All extraction tiers failed for https://conceptkart.com/products/moondrop-chu-ii-chu-2-in-ear-monitor`
**Root Cause:** The Tier 1 HTTP scraper was failing to parse the product page, and the LLM fallback was using an outdated or ineffective model, resulting in all tiers failing to extract data.
**Resolution Strategy:** 
- Upgraded the LLM fallback to use `llama-3.1-8b-instant` via Groq.
- Updated the Site Registry to enable better HTTP-tier extraction for conceptkart.com, Amazon, and HeadphoneZone.
- Completed as part of Epic 4.

### 2. Unicode Encoding Failure
**Status:** RESOLVED
**Date:** 2026-06-07
**Error:** `UnicodeEncodeError: 'charmap' codec can't encode character '\u2717' in position 2: character maps to <undefined>`
**Root Cause:** The console logger or string formatter was attempting to print Unicode characters (`\u2717`, which is ✗) using the default Windows `cp1252` encoding instead of UTF-8.
**Resolution Strategy:** 
- Ensured proper UTF-8 encoding in logging and console output paths to prevent Unicode encode errors during pipeline execution.

## Observability Guidelines
- All new errors are tracked locally in `data/error_logs.json` and optionally stored in the Parquet DLQ (`data/quarantine_*.parquet`).
- The React Frontend `/api/errors` endpoint parses and beautifies these raw error dictionaries in the Extraction Error Log panel for UI readability.
- DLQ spam has been resolved by implementing backend deduplication in the API endpoint.
