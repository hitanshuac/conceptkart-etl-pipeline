import sqlite3

def create_table():
    # 1. Connect to the database
    conn = sqlite3.connect('prices.db') 
    cursor = conn.cursor()

    # 2. Write the SQL DDL
    create_raw_prices_sql = """
    CREATE TABLE IF NOT EXISTS raw_daily_prices (
        product_name TEXT,
        vendor_name TEXT,
        vendor_url TEXT,
        price_current INTEGER,
        scraped_at_utc TEXT
    );
    """
    
    create_tracked_products_sql = """
    CREATE TABLE IF NOT EXISTS tracked_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE NOT NULL,
        target_price INTEGER NOT NULL,
        is_active INTEGER DEFAULT 1
    );
    """

    # 3. Execute and close
    cursor.execute(create_raw_prices_sql)
    cursor.execute(create_tracked_products_sql)
    
    # 4. Seed initial data if empty
    cursor.execute("SELECT COUNT(*) FROM tracked_products")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO tracked_products (url, target_price) VALUES (?, ?)",
            ('https://conceptkart.com/products/moondrop-chu-ii-chu-2-in-ear-monitor', 2000)
        )
        print("Seeded database with initial tracked product.")
        
    conn.commit()
    print("SUCCESS: Infrastructure check passed. Tables are ready.")
    conn.close()

if __name__ == "__main__":
    create_table()