"""
Scheduler daemon using APScheduler.

Replaces the naive time.sleep() loop with a proper scheduler
that supports configurable intervals, staggered execution,
and graceful shutdown.

Falls back to the simple sleep loop if APScheduler is not installed.
"""

import os
import signal
import subprocess
import sys
import time


def run_pipeline():
    """Execute the ETL pipeline as a subprocess.

    Using subprocess ensures a crash in main.py doesn't kill the daemon.
    """
    print("\n" + "=" * 50)
    print(f"Running ETL Pipeline at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per run
        )
        print(result.stdout)
        if result.stderr:
            print(f"ERRORS:\n{result.stderr}")
    except subprocess.TimeoutExpired:
        print("WARNING: Pipeline execution timed out after 5 minutes.")
    except Exception as e:
        print(f"DAEMON ERROR: {e}")


def run_daemon():
    """Start the scheduling daemon.

    Tries APScheduler first (production-grade). Falls back to
    a simple sleep loop if APScheduler is not installed.
    """
    interval_seconds = int(os.environ.get("SCRAPE_INTERVAL_SECONDS", 21600))  # 6 hours default

    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        print(f"Starting APScheduler daemon. Interval: {interval_seconds}s ({interval_seconds // 3600}h)")

        scheduler = BlockingScheduler()
        scheduler.add_job(
            run_pipeline,
            trigger=IntervalTrigger(seconds=interval_seconds),
            id="etl_pipeline",
            name="ETL Pipeline",
            max_instances=1,  # Prevent overlapping runs
            misfire_grace_time=60,
        )

        # Run immediately on startup, then on schedule
        run_pipeline()

        # Graceful shutdown on SIGINT/SIGTERM
        def shutdown(signum, frame):
            print("\nShutting down scheduler...")
            scheduler.shutdown(wait=False)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        scheduler.start()

    except ImportError:
        # Fallback: simple sleep loop (original behavior)
        print(f"Starting simple daemon (APScheduler not installed). Interval: {interval_seconds}s")

        while True:
            try:
                run_pipeline()
            except Exception as e:
                print(f"DAEMON ERROR: {e}")

            print(f"Sleeping for {interval_seconds} seconds...")
            time.sleep(interval_seconds)


if __name__ == "__main__":
    run_daemon()
