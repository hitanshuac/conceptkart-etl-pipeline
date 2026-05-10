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
- **Automated Verification**: Built-in sanity checks to identify pricing anomalies during the ingestion phase.

---

## 🛠️ Technical Stack
- **Language**: Python 3.x
- **Storage**: SQLite
- **Libraries**: `requests`, `sqlite3`

---
**Focus: Data Engineering, Automation, and Scalable Schema Design.** 🛡️✨
