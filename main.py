import db_setup
import extractor
import price_check
import load_data
import notifier
import sqlite3

from load_data import get_supabase_client

def get_tracked_products():
    try:
        supabase = get_supabase_client()
        response = supabase.table('tracked_products').select('id, url, target_price').eq('is_active', True).execute()
        
        # Map list of dicts to list of tuples for backwards compatibility with the loop
        return [(item['id'], item['url'], item['target_price']) for item in response.data]
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return []

def main():
    print("\n--- STARTING ETL PIPELINE ---")
    
    try:
        # 1. Ensure infrastructure exists
        db_setup.create_table()
        
        # 2. Get Targets
        products = get_tracked_products()
        if not products:
            print("No active products to track. Exiting.")
            return

        for prod_id, target_url, target_price in products:
            print(f"\nProcessing [{prod_id}] {target_url} (Target: Rs.{target_price})")
            
            try:
                # 3. Extract
                raw_data = extractor.scrape_conceptkart(target_url) 
                
                # 4. Transform/Validate
                is_valid, is_target_hit = price_check.validate_price_payload(raw_data, target_price)
                
                if is_valid:
                    print(f"Validation passed. Current Price: Rs.{raw_data['price_current']}. Loading to warehouse...")
                    
                    # 5. Load
                    load_data.load_to_database(raw_data, prod_id)
                    
                    # 6. Notify if hit
                    if is_target_hit:
                        notifier.notify_price_drop(
                            raw_data['product_name'], 
                            raw_data['price_current'], 
                            raw_data['vendor_url']
                        )
                    else:
                        print("Target price not hit. No notification sent.")
                        
            except Exception as e:
                print(f"ERROR processing product {prod_id}: {e}")
                
        print("\n--- PIPELINE COMPLETED SUCCESSFULLY ---")
            
    except Exception as e:
        print(f"PIPELINE FAILED: {e}")

if __name__ == "__main__":
    main()