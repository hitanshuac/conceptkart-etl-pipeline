import db_setup
import extractor
import price_check
import load_data

def main():
    try:
        print("\n--- STARTING ETL PIPELINE ---")
        
        # 1. Ensure infrastructure exists
        db_setup.create_table()
        
        # 2. Extract
        raw_data = extractor.scrape_conceptkart() 
        
        # 3. Transform/Validate
        if price_check.validate_price_payload(raw_data):
            print("Validation passed. Loading to warehouse...")
            
            # 4. Load
            load_data.load_to_database(raw_data)
            
        print("--- PIPELINE COMPLETED SUCCESSFULLY ---\n")
            
    except Exception as e:
        print(f"PIPELINE FAILED: {e}")

# This is the trigger that wakes up the Factory Manager
if __name__ == "__main__":
    main()