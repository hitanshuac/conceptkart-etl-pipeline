import os
import threading
import subprocess
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

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
