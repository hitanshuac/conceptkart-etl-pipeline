import argparse
import sys
from load_data import get_supabase_client

def list_targets():
    try:
        supabase = get_supabase_client()
        response = supabase.table("tracked_products").select("id, url, target_price, is_active").execute()
        rows = response.data
        
        print("\n--- Tracked Products ---")
        if not rows:
            print("No products currently tracked.")
        for row in rows:
            status = "ACTIVE" if row.get("is_active") else "INACTIVE"
            print(f"[{row.get('id')}] {status} | Target: Rs.{row.get('target_price')} | URL: {row.get('url')}")
        print("------------------------\n")
    except Exception as e:
        print(f"ERROR: Could not list targets. {e}")

def add_target(url: str, target_price: int):
    try:
        supabase = get_supabase_client()
        response = supabase.table("tracked_products").insert({
            "url": url,
            "target_price": target_price,
            "is_active": True
        }).execute()
        
        # Check if insert was successful
        if response.data:
            print(f"SUCCESS: Added {url} with target Rs.{target_price}")
        else:
            print(f"ERROR: Failed to add {url}")
    except Exception as e:
        if "duplicate key value violates unique constraint" in str(e).lower():
            print("ERROR: This URL is already being tracked.")
        else:
            print(f"ERROR: Could not add target. {e}")

def remove_target(target_id: int):
    try:
        supabase = get_supabase_client()
        response = supabase.table("tracked_products").delete().eq("id", target_id).execute()
        if response.data:
            print(f"SUCCESS: Removed product ID {target_id}")
        else:
            print(f"ERROR: No product found with ID {target_id}")
    except Exception as e:
        print(f"ERROR: Could not remove target. {e}")

def toggle_target(target_id: int, is_active: bool):
    try:
        supabase = get_supabase_client()
        response = supabase.table("tracked_products").update({"is_active": is_active}).eq("id", target_id).execute()
        if response.data:
            status = "activated" if is_active else "deactivated"
            print(f"SUCCESS: Product ID {target_id} has been {status}.")
        else:
            print(f"ERROR: No product found with ID {target_id}")
    except Exception as e:
        print(f"ERROR: Could not toggle target. {e}")

def main():
    parser = argparse.ArgumentParser(description="Manage ETL Tracked Products in Supabase")
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List
    subparsers.add_parser('list', help='List all tracked products')

    # Add
    parser_add = subparsers.add_parser('add', help='Add a new product to track')
    parser_add.add_argument('url', type=str, help='Product URL')
    parser_add.add_argument('price', type=int, help='Target Price (in Rs.)')

    # Remove
    parser_rm = subparsers.add_parser('remove', help='Remove a tracked product')
    parser_rm.add_argument('id', type=int, help='Product ID to remove')

    # Disable
    parser_disable = subparsers.add_parser('disable', help='Pause tracking for a product')
    parser_disable.add_argument('id', type=int, help='Product ID to disable')

    # Enable
    parser_enable = subparsers.add_parser('enable', help='Resume tracking for a product')
    parser_enable.add_argument('id', type=int, help='Product ID to enable')

    args = parser.parse_args()

    if args.command == 'list':
        list_targets()
    elif args.command == 'add':
        add_target(args.url, args.price)
    elif args.command == 'remove':
        remove_target(args.id)
    elif args.command == 'disable':
        toggle_target(args.id, False)
    elif args.command == 'enable':
        toggle_target(args.id, True)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
