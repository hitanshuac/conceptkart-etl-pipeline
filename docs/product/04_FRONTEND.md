# Frontend Architecture Document

**Project:** ConceptKart ETL Pipeline v2.0
**Status:** Approved

## 1. Overview
The presentation layer is decoupled from the extraction pipeline. It is a React-based application hosted in the `/dashboard` directory.

## 2. Technology Stack
- **Framework:** React / Vite
- **Styling:** CSS
- **Data Fetching:** Supabase JS SDK

## 3. Integration Points
- Connects directly to the `tracked_products` and `raw_daily_prices` views in Supabase.
- Bypasses the Python backend entirely for data read operations, ensuring high availability even if the scraping node is offline.
