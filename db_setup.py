import sqlite3

def create_table():
    # 1. Connect to the database
    conn = sqlite3.connect('prices.db') 
    cursor = conn.cursor()

    # 2. Write the SQL DDL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS raw_daily_prices (
        product_name TEXT,
        vendor_name TEXT,
        vendor_url TEXT,
        price_current INTEGER,
        scraped_at_utc TEXT
    );
    """

    # 3. Execute and close
    cursor.execute(create_table_sql)
    conn.commit()
    print("SUCCESS: Infrastructure check passed. Table 'raw_daily_prices' is ready.")
    conn.close()

if __name__ == "__main__":
    create_table()