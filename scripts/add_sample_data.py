#!/usr/bin/env python3
"""
Add sample product data to database for testing
Authors: Simarpreet Singh, Param Patel, Allister Mcgregor
"""

import sqlite3
import os

def add_sample_products():
    """Add sample products to the local cache database"""
    
    # Database in project root directory
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create table if not exists
    c.execute('''
    CREATE TABLE IF NOT EXISTS products (
        barcode TEXT PRIMARY KEY,
        name TEXT,
        calories INTEGER,
        fat REAL,
        protein REAL,
        carbs REAL,
        allergens TEXT,
        healthier_alternative TEXT,
        fiber REAL,
        sugar REAL,
        sodium REAL
    )
    ''')
    
    # Sample products
    sample_products = [
        {
            'barcode': '1234567890',
            'name': 'Organic Whole Wheat Bread',
            'calories': 250,
            'fat': 3.0,
            'protein': 8.0,
            'carbs': 45.0,
            'allergens': 'gluten,wheat',
            'healthier_alternative': 'Multigrain Bread (230 cal)',
            'fiber': 6.0,
            'sugar': 4.0,
            'sodium': 380.0
        },
        {
            'barcode': '9876543210',
            'name': 'Chocolate Chip Cookies',
            'calories': 480,
            'fat': 22.0,
            'protein': 5.0,
            'carbs': 65.0,
            'allergens': 'gluten,dairy,eggs',
            'healthier_alternative': 'Oatmeal Cookies (350 cal)',
            'fiber': 2.0,
            'sugar': 32.0,
            'sodium': 420.0
        },
        {
            'barcode': '5551234567',
            'name': 'Greek Yogurt',
            'calories': 100,
            'fat': 0.5,
            'protein': 17.0,
            'carbs': 6.0,
            'allergens': 'dairy',
            'healthier_alternative': 'None',
            'fiber': 0.0,
            'sugar': 4.0,
            'sodium': 65.0
        },
        {
            'barcode': '7778889999',
            'name': 'Potato Chips',
            'calories': 540,
            'fat': 34.0,
            'protein': 7.0,
            'carbs': 52.0,
            'allergens': 'None',
            'healthier_alternative': 'Baked Chips (380 cal)',
            'fiber': 4.0,
            'sugar': 2.0,
            'sodium': 680.0
        },
        {
            'barcode': '1112223334',
            'name': 'Almond Milk',
            'calories': 30,
            'fat': 2.5,
            'protein': 1.0,
            'carbs': 1.0,
            'allergens': 'tree nuts',
            'healthier_alternative': 'None',
            'fiber': 1.0,
            'sugar': 0.0,
            'sodium': 180.0
        },
        {
            'barcode': '4445556667',
            'name': 'Granola Bar',
            'calories': 190,
            'fat': 7.0,
            'protein': 4.0,
            'carbs': 29.0,
            'allergens': 'gluten,tree nuts',
            'healthier_alternative': 'Protein Bar (160 cal)',
            'fiber': 3.0,
            'sugar': 12.0,
            'sodium': 140.0
        },
        {
            'barcode': '0123456789',
            'name': 'Canned Soup',
            'calories': 220,
            'fat': 11.0,
            'protein': 8.0,
            'carbs': 22.0,
            'allergens': 'gluten,dairy',
            'healthier_alternative': 'Low Sodium Soup (180 cal)',
            'fiber': 4.0,
            'sugar': 6.0,
            'sodium': 890.0
        },
        {
            'barcode': '9998887776',
            'name': 'Energy Drink',
            'calories': 110,
            'fat': 0.0,
            'protein': 0.0,
            'carbs': 28.0,
            'allergens': 'None',
            'healthier_alternative': 'Green Tea (2 cal)',
            'fiber': 0.0,
            'sugar': 27.0,
            'sodium': 200.0
        },
        {
            'barcode': '6667778889',
            'name': 'Peanut Butter',
            'calories': 588,
            'fat': 50.0,
            'protein': 25.0,
            'carbs': 20.0,
            'allergens': 'peanuts',
            'healthier_alternative': 'Almond Butter (614 cal)',
            'fiber': 6.0,
            'sugar': 9.0,
            'sodium': 476.0
        },
        {
            'barcode': '3334445556',
            'name': 'Orange Juice',
            'calories': 110,
            'fat': 0.0,
            'protein': 2.0,
            'carbs': 26.0,
            'allergens': 'None',
            'healthier_alternative': 'Fresh Squeezed OJ (112 cal)',
            'fiber': 0.5,
            'sugar': 21.0,
            'sodium': 5.0
        }
    ]
    
    # Insert products
    for product in sample_products:
        try:
            c.execute('''
            INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                product['barcode'],
                product['name'],
                product['calories'],
                product['fat'],
                product['protein'],
                product['carbs'],
                product['allergens'],
                product['healthier_alternative'],
                product['fiber'],
                product['sugar'],
                product['sodium']
            ))
            print(f"✅ Added: {product['name']} ({product['barcode']})")
        except Exception as e:
            print(f"❌ Error adding {product['name']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 Successfully added {len(sample_products)} sample products!")
    print("\nTest barcodes:")
    for product in sample_products:
        print(f"  - {product['barcode']}: {product['name']}")
    print("\nYou can now run: python scanner_app.py")

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Sample Product Data")
    print("=" * 60)
    print()
    add_sample_products()
    print("\n" + "=" * 60)
