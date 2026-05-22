from load_data import get_supabase_client

def create_table():
    try:
        supabase = get_supabase_client()
        # Test connection by querying tracked_products table
        supabase.table('tracked_products').select('count', count='exact').limit(1).execute()
        print("SUCCESS: Infrastructure check passed. Connected to Supabase.")
    except Exception as e:
        print(f"ERROR: Could not connect to Supabase. Details: {e}")

if __name__ == "__main__":
    create_table()