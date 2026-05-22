import os
from supabase import create_client
from dotenv import load_dotenv

def get_supabase_client():
    # Load the .env file from the dashboard directory if it exists
    load_dotenv(os.path.join(os.path.dirname(__file__), 'dashboard', '.env'))
    
    url = os.environ.get("VITE_SUPABASE_URL", "")
    key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
    
    if url and not url.startswith('http'):
        url = f"https://{url}.supabase.co"
        
    if not url or not key:
        raise ValueError("Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in environment variables")
        
    return create_client(url, key)

def load_to_database(payload: dict, tracked_product_id: int):
    try:
        supabase = get_supabase_client()
        
        # Insert into raw_daily_prices
        response = supabase.table('raw_daily_prices').insert({
            'tracked_product_id': tracked_product_id,
            'product_name': payload.get('product_name'),
            'vendor_name': payload.get('vendor_name'),
            'vendor_url': payload.get('vendor_url'),
            'price_current': payload.get('price_current'),
            'scraped_at_utc': payload.get('scraped_at_utc')
        }).execute()
        
        print("SUCCESS: Row inserted into Supabase raw_daily_prices")
        
    except Exception as e:
        print(f"FATAL DB ERROR: Could not insert row. Details: {e}")
        # Here is where our Slack Webhook would fire