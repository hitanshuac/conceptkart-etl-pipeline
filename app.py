import os
import subprocess
import threading

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()


# 1. Start the scraper daemon in a background thread
def run_scraper_daemon():
    print("Starting background scraper daemon...")
    subprocess.run(["python", "daemon.py"])


daemon_thread = threading.Thread(target=run_scraper_daemon, daemon=True)
daemon_thread.start()

# 2. Serve the React Dashboard
# Ensure the dashboard has been built (npm run build)
dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard", "dist")

if os.path.exists(dashboard_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(dashboard_path, "assets")), name="assets")

    @app.get("/api/errors")
    def get_errors():
        """Reads the local Parquet DLQ and returns the 10 most recent errors."""
        import glob

        try:
            import pyarrow.parquet as pq
        except ImportError:
            return {"error": "pyarrow not installed"}

        data_dir = os.path.join(os.path.dirname(__file__), "data")
        parquet_files = glob.glob(os.path.join(data_dir, "quarantine_*.parquet"))
        if not parquet_files:
            return {"errors": []}

        # Get the most recent parquet file
        latest_file = max(parquet_files, key=os.path.getctime)
        try:
            table = pq.read_table(latest_file)
            records = table.to_pylist()

            # Deduplicate by (source_url, error_message), keeping the most recent
            records.sort(key=lambda x: x.get("timestamp_utc", ""), reverse=True)
            seen = set()
            deduped = []
            for r in records:
                key = (r.get("source_url"), r.get("error_message"))
                if key not in seen:
                    seen.add(key)
                    deduped.append(r)
                if len(deduped) >= 10:
                    break

            return {"errors": deduped}
        except Exception as e:
            return {"error": str(e)}

    @app.get("/")
    def read_index():
        return FileResponse(os.path.join(dashboard_path, "index.html"))

    @app.get("/{catchall:path}")
    def serve_spa(catchall: str):
        return FileResponse(os.path.join(dashboard_path, "index.html"))
else:

    @app.get("/")
    def read_index():
        return {"error": "Dashboard build not found. Please run 'npm run build' in the dashboard directory."}


if __name__ == "__main__":
    import uvicorn

    # Bind to 7860 as required by Hugging Face Spaces
    uvicorn.run(app, host="0.0.0.0", port=7860)
