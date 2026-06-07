import load_data

supabase = load_data.get_supabase_client()
res = supabase.table("tracked_products").select("*").execute()
print(res.data)
