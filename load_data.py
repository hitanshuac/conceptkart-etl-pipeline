import os

from dotenv import load_dotenv
from supabase import create_client

from price_check import _quarantine_record


def get_supabase_client():
    # Load from dashboard/.env since that's where Vite keeps credentials
    env_path = os.path.join(os.path.dirname(__file__), "dashboard", ".env")
    load_dotenv(env_path)

    # 12-Factor config: use os.environ instead of hardcoded .env path
    url = os.environ.get("VITE_SUPABASE_URL", "")
    key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

    if url and not url.startswith("http"):
        url = f"https://{url}.supabase.co"

    if not url or not key:
        raise ValueError("Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in environment variables")

    return create_client(url, key)


def load_to_database(payload: dict, tracked_product_id: int):
    try:
        supabase = get_supabase_client()

        # Upsert into raw_daily_prices to guarantee idempotency
        response = (
            supabase.table("raw_daily_prices")
            .upsert(
                {
                    "tracked_product_id": tracked_product_id,
                    "product_name": payload.get("product_name"),
                    "vendor_name": payload.get("vendor_name"),
                    "vendor_url": payload.get("vendor_url"),
                    "price_current": payload.get("price_current"),
                    "scraped_at_utc": payload.get("scraped_at_utc"),
                }
            )
            .execute()
        )

        print(f"  [LOADER] SUCCESS: Row inserted into Supabase for ID {tracked_product_id}")

    except Exception as e:
        print(f"  [LOADER] FATAL DB ERROR: Could not insert row. Routing to DLQ. Details: {e}")
        # Store-and-Forward fallback: don't lose the data, queue it!
        payload["tracked_product_id"] = tracked_product_id  # ensure we know where it belongs
        _quarantine_record(payload, "SupabaseUploadFailed", str(e))
