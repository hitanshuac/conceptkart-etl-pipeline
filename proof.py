import sqlite3

# 1. Connect to the warehouse you built
conn = sqlite3.connect('prices.db')
cursor = conn.cursor()

# 2. Write a standard Analyst SQL query
cursor.execute("SELECT * FROM raw_daily_prices;")

# 3. Fetch all the rows and print them raw
rows = cursor.fetchall()

print("\n--- PHYSICAL DATA IN WAREHOUSE ---")
for row in rows:
    print(row)
print("----------------------------------\n")

conn.close()