import sqlite3
import argparse
import sys

DB_PATH = 'prices.db'

def get_connection():
    return sqlite3.connect(DB_PATH)

def list_targets():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, url, target_price, is_active FROM tracked_products")
        rows = cursor.fetchall()
        
        print("\n--- Tracked Products ---")
        if not rows:
            print("No products currently tracked.")
        for row in rows:
            status = "ACTIVE" if row[3] else "INACTIVE"
            print(f"[{row[0]}] {status} | Target: Rs.{row[2]} | URL: {row[1]}")
        print("------------------------\n")

def add_target(url: str, target_price: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO tracked_products (url, target_price) VALUES (?, ?)",
                (url, target_price)
            )
            conn.commit()
            print(f"SUCCESS: Added {url} with target Rs.{target_price}")
        except sqlite3.IntegrityError:
            print("ERROR: This URL is already being tracked.")

def remove_target(target_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tracked_products WHERE id = ?", (target_id,))
        if cursor.rowcount > 0:
            conn.commit()
            print(f"SUCCESS: Removed product ID {target_id}")
        else:
            print(f"ERROR: No product found with ID {target_id}")

def toggle_target(target_id: int, is_active: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tracked_products SET is_active = ? WHERE id = ?", (is_active, target_id))
        if cursor.rowcount > 0:
            conn.commit()
            status = "activated" if is_active else "deactivated"
            print(f"SUCCESS: Product ID {target_id} has been {status}.")
        else:
            print(f"ERROR: No product found with ID {target_id}")

def main():
    parser = argparse.ArgumentParser(description="Manage ETL Tracked Products")
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
        toggle_target(args.id, 0)
    elif args.command == 'enable':
        toggle_target(args.id, 1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
