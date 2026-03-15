import sqlite3

# 1. Connect to the database
conn = sqlite3.connect('prices.db') 

# 2. Create the cursor
cursor = conn.cursor()

# 3. Write the SQL DDL (Fill in the blanks!)
create_table_sql = """
CREATE TABLE IF NOT EXISTS raw_daily_prices (
    product_name TEXT,
    vendor_name TEXT,
    vendor_url TEXT,
    price_current INTEGER,
    scraped_at_utc TEXT
);
"""

# 4. Execute the SQL and commit (save) the changes
cursor.execute(create_table_sql)
conn.commit()

print("Table 'raw_daily_prices' created successfully!")

# 5. Always close the connection
conn.close()