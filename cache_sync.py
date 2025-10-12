import sqlite3, requests, json, os

db_path = os.path.join(os.path.dirname(__file__), "cache.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS products (
    barcode TEXT PRIMARY KEY,
    name TEXT,
    calories INTEGER,
    fat REAL,
    protein REAL,
    carbs REAL,
    allergens TEXT,
    healthier_alternative TEXT
)
''')

try:
    print("Fetching products from server...")
    resp = requests.get("http://localhost/smartscanner/getAllProducts.php", timeout=5)
    data = resp.json()
    for item in data:
        c.execute('''
        INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?)
        ''', (item['barcode'], item['name'], item['calories'], item['fat'], item['protein'],
              item['carbs'], item['allergens'], item['healthier_alternative']))
    conn.commit()
    print("✅ Cache synced successfully!")
except Exception as e:
    print(f"⚠️ Offline mode - using cached data. Error: {e}")

conn.close()
