import load_data

supabase = load_data.get_supabase_client()
res = supabase.table("dashboard_view").select("*").execute()
print(res.data)
