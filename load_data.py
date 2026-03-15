import sqlite3

def load_to_database(payload: dict):
    conn = None
    try:
        conn = sqlite3.connect('prices.db')
        cursor = conn.cursor()
        
        insert_sql = """
        INSERT INTO raw_daily_prices (product_name, vendor_name, vendor_url, price_current, scraped_at_utc)
        VALUES (?, ?, ?, ?, ?)
        """
        values = tuple(payload.values())
        
        cursor.execute(insert_sql, values)
        conn.commit()
        print("SUCCESS: Row inserted into prices.db")
        
    except sqlite3.Error as e:
        print(f"FATAL DB ERROR: Could not insert row. Details: {e}")
        # Here is where our Slack Webhook would fire
        
    finally:
        # This ALWAYS runs, even if the try block crashes.
        if conn:
            conn.close()
            print("Database connection safely closed.")