import time
import os
import subprocess

def run_daemon():
    # Run every 6 hours by default (21600 seconds)
    interval_seconds = int(os.environ.get('SCRAPE_INTERVAL_SECONDS', 21600))
    print(f"Starting ConceptKart ETL Daemon. Interval: {interval_seconds} seconds.")
    
    while True:
        try:
            print("\n" + "="*50)
            print(f"Running ETL Pipeline at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*50)
            
            # Use subprocess so a crash in main.py doesn't kill the daemon
            result = subprocess.run(["python", "main.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print(f"ERRORS:\n{result.stderr}")
                
        except Exception as e:
            print(f"DAEMON ERROR: {e}")
            
        print(f"Sleeping for {interval_seconds} seconds...")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_daemon()
