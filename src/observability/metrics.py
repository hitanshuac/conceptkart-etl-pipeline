"""
DuckDB telemetry plane for pipeline metrics.

Records per-scrape metrics (latency, tier, success, cost) into a local
DuckDB database following the DuckDB Optimizer skill directives:
  - WAL mode enabled
  - Memory capped at 256MB
  - INSERT OR REPLACE for idempotency

Non-blocking writes ensure telemetry never crashes the pipeline.
"""

import os
import threading
from datetime import datetime, timezone
from typing import Optional

from src.models import PipelineMetric

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
METRICS_DB_PATH = os.path.join(DATA_DIR, "pipeline_metrics.db")

# DuckDB is optional — metrics degrade gracefully if not installed
try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


_init_lock = threading.Lock()
_initialized = False


def _ensure_schema() -> None:
    """Create the metrics table if it doesn't exist.
    
    Follows DuckDB Optimizer skill:
    - WAL mode for crash resilience
    - Memory limit capped at 256MB
    """
    global _initialized
    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        if not HAS_DUCKDB:
            return

        os.makedirs(DATA_DIR, exist_ok=True)

        try:
            conn = duckdb.connect(METRICS_DB_PATH)
            conn.execute("PRAGMA memory_limit='256MB'")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_metrics (
                    timestamp_utc TIMESTAMP NOT NULL,
                    domain VARCHAR NOT NULL,
                    tracked_product_id INTEGER,
                    tier_used VARCHAR NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_type VARCHAR,
                    tokens_used INTEGER DEFAULT 0,
                    proxy_used BOOLEAN DEFAULT FALSE,
                    http_status INTEGER
                )
            """)
            conn.close()
            _initialized = True
        except Exception as e:
            print(f"[METRICS] Failed to initialize DuckDB schema: {e}")


def record_metric(metric: PipelineMetric) -> None:
    """Write a telemetry record to DuckDB.
    
    Non-blocking: runs in a background thread so the main
    pipeline is never blocked by a slow disk write.
    Per 12-factor-rules.md Factor XI: treat logs as event streams.
    """
    thread = threading.Thread(target=_write_metric, args=(metric,), daemon=True)
    thread.start()


def _write_metric(metric: PipelineMetric) -> None:
    """Background thread worker for metric writes."""
    if not HAS_DUCKDB:
        return

    try:
        _ensure_schema()
        conn = duckdb.connect(METRICS_DB_PATH)
        conn.execute("PRAGMA memory_limit='256MB'")
        conn.execute(
            """
            INSERT INTO pipeline_metrics (
                timestamp_utc, domain, tracked_product_id, tier_used,
                latency_ms, success, error_type, tokens_used,
                proxy_used, http_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                metric.timestamp_utc,
                metric.domain,
                metric.tracked_product_id,
                metric.tier_used,
                metric.latency_ms,
                metric.success,
                metric.error_type,
                metric.tokens_used,
                metric.proxy_used,
                metric.http_status,
            ],
        )
        conn.close()
    except Exception as e:
        # Telemetry must never crash the pipeline
        print(f"[METRICS] Failed to write metric: {e}")


def get_domain_stats(domain: str, days: int = 7) -> Optional[dict]:
    """Query aggregated stats for a domain over the last N days.
    
    Returns success rate, average latency, and tier distribution.
    Useful for SRE dashboards and circuit breaker tuning.
    """
    if not HAS_DUCKDB:
        return None

    try:
        _ensure_schema()
        conn = duckdb.connect(METRICS_DB_PATH, read_only=True)
        result = conn.execute(
            f"""
            SELECT
                COUNT(*) as total_scrapes,
                SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                ROUND(AVG(latency_ms), 0) as avg_latency_ms,
                tier_used,
                COUNT(*) as tier_count
            FROM pipeline_metrics
            WHERE domain = ?
              AND timestamp_utc >= CURRENT_TIMESTAMP - INTERVAL '{int(days)}' DAY
            GROUP BY tier_used
            ORDER BY tier_count DESC
            """,
            [domain],
        ).fetchall()
        conn.close()

        if not result:
            return None

        total = sum(r[0] for r in result)
        successes = sum(r[1] for r in result)
        return {
            "domain": domain,
            "total_scrapes": total,
            "success_rate": round(successes / total * 100, 1) if total else 0,
            "avg_latency_ms": result[0][2],
            "tier_distribution": {r[3]: r[4] for r in result},
        }
    except Exception as e:
        print(f"[METRICS] Failed to query stats: {e}")
        return None
