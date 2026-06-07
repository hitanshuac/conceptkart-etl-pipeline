# ConceptKart ETL Pipeline 🛒📊

![Architecture Diagram](docs/assets/architecture_diagram_showcase.png)

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
- **100% Core Test Coverage**: Fully verified Pydantic boundaries and database idempotency.
- **Pydantic Validation & DLQ**: Strict data contracts ensure corrupt data never enters Supabase. Validation failures trigger a Store-and-Forward mechanism, saving payloads to a local Parquet Dead-Letter Queue for automatic retry.
- **DuckDB Telemetry**: A local `.db` file powered by DuckDB captures deep analytics on pipeline performance, latency, and extraction success rates.

---

## 🔄 Technical Flow

```mermaid
graph TD
    A[Scheduler Trigger] --> B[Tier 1: curl-cffi]
    B -->|Failed| C[Tier 2: Crawl4AI]
    C -->|Failed| D[Tier 3: LLM Self-Healing]
    B -->|Success| E[Pydantic Validation]
    C -->|Success| E
    D -->|Success| E
    E -->|Valid| F[Supabase Upsert]
    E -->|Invalid| G[Parquet DLQ]
    F -->|Network Error| G
```

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
- **AI Models**: Llama-3.1-8B-Instant (via Groq/OpenRouter/HF)

---

## ⚙️ Configuration & Setup

Set the following environment variables in your local `dashboard/.env` file. (The Python backend automatically sources credentials from the dashboard's environment to ensure parity).

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

---

## 🧪 Local Development & Testing Guide

To test the system end-to-end, follow these steps:

### 1. Start the React Dashboard
The dashboard allows you to visualize the data in real-time.
```bash
# Navigate to the dashboard directory
cd dashboard

# Install dependencies
npm install

# Start the Vite development server
npm run dev
```
Open your browser to `http://localhost:5173`. You should see the UI. If no data exists, it will prompt you to run the initial scrape.

### 2. Add a Tracking Target
You can add a product to track either through the Dashboard UI, or via the Python CLI. Open a new terminal window at the root of the project:
```bash
# Add a product to track (Target price: Rs. 17000)
python manage_targets.py add "https://conceptkart.com/products/shanling-eh1-desktop-dac-and-headphone-amplifier" 17000

# Verify it was added to the Supabase tracking queue
python manage_targets.py list
```

### 3. Run the Backend Extraction Pipeline
Manually trigger the scraper to extract data, validate it, and push it to Supabase.
```bash
python main.py
```
*Watch the terminal logs. You will see the 3-Tier Cascade execute. If the price matches the target, it will trigger the Notifier.*

### 4. Verify in the Dashboard
Once `main.py` finishes:
1. Go back to your browser `http://localhost:5173`.
2. Refresh the page. You should now see the product listed, its current price, and the historical trend chart populated with the newly scraped data point!

### 5. Running Continuously (Production)
To run the scraper continuously in the background locally (default: every 6 hours):
```bash
python daemon.py
```

### 6. Cloud Deployment (Hugging Face Spaces)
To deploy the pipeline to run autonomously 24/7 for free:
1. Create a Docker Space on Hugging Face.
2. Set your `HF_SPACE_REPO` and `HF_TOKEN` environment variables.
3. Run the upload script:
```bash
python upload_to_hf.py
```
*This deploys a unified container that serves the React Dashboard on port `7860` while running the scraper daemon in the background.*

---

## 🧬 How to Adopt This Environment (Injection Method)
To test if this environment works as intended in your own projects, you do not need to rewrite your entire codebase. Instead, you inject the "Agentic Brain":

1. **Pull the Brain:** Copy the `.agents/` directory and the `HANDOVER.md` file from this repository into the root of your existing project.
2. **Summon the Agent:** Open your AI coding assistant (e.g., Cursor, Windsurf, or an Antigravity agent) in your project.
3. **Trigger the Handover:** Send your AI the following prompt:
   > *"Please read `@HANDOVER.md`. You must acknowledge the architecture constraints and the strict Rule 00 (No Unauthorized Deletions). Your absolute first action must be to execute `.agents/workflows/merge-conflict-resolution.md` to safely resolve any file collisions. Once I have manually approved the merge, proceed to `BOOTSTRAP.MD`."*
4. **Watch it Work:** The AI will automatically parse the strict governance rules, apply the context compactor, and begin aligning your legacy code to the production standards defined in `.agents/rules/`.

---
**Focus: Data Engineering, AI Self-Healing, and Scalable Agentic Architecture.** 🛡️✨

---
[View Agentic Environment Documentation](AGENT_DOCS.md)
