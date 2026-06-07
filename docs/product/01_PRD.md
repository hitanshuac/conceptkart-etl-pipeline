# Product Requirements Document (PRD)

**Project Name:** ConceptKart ETL Pipeline v2.0
**Date:** 2026-06-07
**Status:** Approved

## 1. Objective
To build a highly resilient, zero-cost, site-agnostic pricing engine that tracks e-commerce products dynamically. It must bypass bot protections and ensure zero data loss during cloud database outages.

## 2. Target Audience / Personas
- **Data Engineers / SREs:** Needing a robust, observable architecture with clear boundaries between the Control Plane and Application Plane.
- **Business Analysts:** Requiring accurate, daily historical pricing data stored reliably in a cloud Postgres instance (Supabase) for dashboarding.

## 3. Core Features (MVP)
1. **3-Tier Extraction Cascade:** Fallback from fast HTTP scraping, to Headless Browser, to AI-driven data extraction.
2. **Store-and-Forward DLQ:** Local Parquet-based quarantine queue to hold failed payloads if Supabase is down, ensuring zero data loss.
3. **Idempotent Cloud Upserts:** `UPSERT` operations to prevent duplicate daily tracking records.
4. **React Dashboard:** A UI to monitor tracking targets and view historical price trends.

## 4. Out of Scope (Non-Goals)
- Fully distributed scraping across cloud container fleets (Pipeline must remain capable of running on a single local daemon/server).
- High-frequency tick-level data (Frequency is restricted to daily/hourly to respect rate limits).

## 5. Success Metrics
- **99%+ Extraction Success Rate:** Handled via the Tier 3 LLM fallback mechanism.
- **Zero Data Loss:** Validated through DLQ replay tests.
- **Zero Maintenance Cloud:** Supabase and automated GitHub actions keep the engine running seamlessly.
