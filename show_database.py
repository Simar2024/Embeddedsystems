import sqlite3

def show_database():
    conn = sqlite3.connect('nutrition_cache.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables in database:", tables)
    
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    
    print("\n=== PRODUCTS ===")
    for row in rows:
        print(row)
    
    conn.close()

show_database()