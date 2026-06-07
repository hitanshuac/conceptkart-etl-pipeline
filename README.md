# ConceptKart ETL Pipeline 🛒📊

![System Architecture](docs/assets/architecture_diagram.png)

A production-grade, Agentic ETL (Extract, Transform, Load) pipeline designed to dynamically track, analyze, and alert on e-commerce pricing data. This project demonstrates high-availability architecture, strict SRE data governance, and autonomous self-healing capabilities.

---

## 🏛️ Architecture: The Split-Plane Environment

This repository is built as an **Antigravity Base Agentic Environment**, featuring a strict separation between the AI Control Plane and the Application Plane.

### 1. The Cloud Data Plane (Supabase & React)
- **Supabase (PostgreSQL)**: Serves as the central cloud database for `tracked_products` and `raw_daily_prices`.
- **React Dashboard**: A separate frontend UI (located in `/dashboard`) that provides a user-friendly interface to view historical price charts and manage tracking targets.

### 2. The Extraction Cascade (Python Agent)
The backend pipeline operates a **3-Tier Fallback Cascade** to guarantee 99%+ scraping success rates without getting blocked:
- **Tier 1 (curl-cffi)**: High-speed TLS HTTP impersonation using Open Graph and JSON-LD parsing.
- **Tier 2 (Crawl4AI + Playwright)**: Stealth browser rendering for JavaScript-heavy single-page applications.
- **Tier 3 (LLM Self-Healing)**: AI-driven extraction (via Groq/OpenRouter/HuggingFace) that automatically bypasses layout redesigns and structural changes.

### 3. SRE & Observability Plane
- **Pydantic Validation & DLQ**: Strict data contracts ensure corrupt data never enters Supabase. Validation failures trigger a Store-and-Forward mechanism, saving payloads to a local Parquet Dead-Letter Queue for automatic retry.
- **DuckDB Telemetry**: A local `.db` file powered by DuckDB captures deep analytics on pipeline performance, latency, and extraction success rates without blocking the main event loop.
- **AST-Compressed Error Logs**: All exceptions are parsed by `jCodeMunch` and logged as structured JSON to maintain a highly compressed context window for autonomous debugging.

---

## 🚀 Key Features
- **Idempotent Data Ingestion**: Uses `UPSERT` conflict resolution to prevent duplicate records during network retries.
- **Zero Data Loss Guarantee**: A Store-and-Forward retry loop checks for failed cloud uploads on every startup.
- **Anti-Bot Evasion**: Randomized residential User-Agents, TLS fingerprinting, and per-domain rate limiting.
- **Multi-Channel Alerts**: Built-in alerting to trigger instant **Telegram Bot** and **Webhook** notifications when target prices are hit.

---

## 🛠️ Technical Stack
- **Languages**: Python 3.11+ / JavaScript (React)
- **Cloud Database**: Supabase (Postgres)
- **Local Analytics**: DuckDB & PyArrow (Parquet)
- **Extraction**: `curl-cffi`, `Crawl4AI`, `BeautifulSoup4`
- **Orchestration**: `APScheduler`
- **AI Models**: Llama-3-8B (via Groq/OpenRouter/HF)

---

## ⚙️ Configuration & Setup

Set the following environment variables in your local `.env` or `dashboard/.env` file:

```env
# Cloud Database (Required)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key

# LLM Fallback Provider (Pick one - Required for Tier 3)
GROQ_API_KEY=gsk_...
# OPENROUTER_API_KEY=sk-or-...
# HF_API_KEY=hf_...

# Notifications (Optional)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
WEBHOOK_URL=https://hooks.slack.com/...
```

## 💻 Usage

**1. Manage Tracking Targets**
You can add tracking targets via the React Dashboard or directly through the synchronized CLI:
```bash
python manage_targets.py add "https://conceptkart.com/products/example-iem" 2000
python manage_targets.py list
```

**2. Run the Pipeline**
Run a single batch scrape:
```bash
python main.py
```
Or start the continuous scheduling daemon (runs every 6 hours by default):
```bash
python daemon.py
```

---
**Focus: Data Engineering, AI Self-Healing, and Scalable Agentic Architecture.** 🛡️✨
