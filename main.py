import load_data
import price_check
import db_setup
import extractor # Assuming your web scraper is saved here

def main():
    try:
        print("Starting Daily ETL Pipeline...")
        
        # 1. Ensure the infrastructure exists
        db_setup.create_table()
        
        # 2. Extract (Pulling from the web)
        raw_data = extractor.scrape_conceptkart() 
        
        # 3. Transform & Validate (The Tripwire)
        if price_check.validate_price_payload(raw_data):
            print("Validation passed.")
            
            # 4. Load (Pushing to SQLite)
            load_data.load_to_database(raw_data)
            print("Pipeline completed successfully.")
            
    except Exception as e:
        # If ANY step above fails, it immediately jumps here
        print(f"PIPELINE FAILED: {e}")
        # send_slack_webhook(f"PIPELINE FAILED: {e}")

if __name__ == "__main__":
    main()