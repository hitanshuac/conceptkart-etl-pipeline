# ConceptKart ETL Pipeline 🛒📊

A lightweight, modular ETL (Extract, Transform, Load) pipeline designed to track and analyze e-commerce pricing data. This project demonstrates clean data engineering patterns and automated SQLite state management.

---

## 🏛️ Architecture: Modular Data Flow
The pipeline is designed with a strict separation of concerns:
1. **Extraction (`extractor.py`)**: Fetches raw pricing data from e-commerce sources.
2. **Setup (`db_setup.py`)**: Handles the creation and schema migration of the local SQLite store.
3. **Load (`load_data.py`)**: Transforms raw data and performs atomic insertions into the relational store.
4. **Validation (`price_check.py`)**: Real-time analysis of pricing trends and data integrity verification.

---

## 🚀 Key Features
- **Atomic Loading**: Ensures that data ingestion is idempotent and crash-resilient.
- **Relational Integrity**: Utilizes SQLite for a zero-configuration, high-performance local data store.
- **Automated Verification & Alerts**: Built-in sanity checks to identify pricing anomalies and trigger instant **Telegram Bot Notifications** when target prices are hit.

---

## 🛠️ Technical Stack
- **Language**: Python 3.x
- **Storage**: SQLite
- **Libraries**: `requests`, `beautifulsoup4`
- **Alerts**: Telegram Bot API

---

## ⚙️ Configuration
Set the following environment variables before running the pipeline:
- `CONCEPTKART_URL`: Target product URL
- `TARGET_PRICE`: The price threshold for alerts (e.g., `2000`)
- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
- `TELEGRAM_CHAT_ID`: Your Telegram Chat ID

---
**Focus: Data Engineering, Automation, and Scalable Schema Design.** 🛡️✨
