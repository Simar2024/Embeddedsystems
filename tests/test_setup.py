#!/usr/bin/env python3
"""
Test script to verify system setup
Checks dependencies and basic functionality
"""

import sys
import subprocess

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except ImportError:
        pkg = package_name or module_name
        print(f"❌ {module_name} - Missing (install with: pip install {pkg})")
        return False

def test_opencv():
    """Test OpenCV and display version"""
    try:
        import cv2
        print(f"✅ OpenCV - OK (version {cv2.__version__})")
        
        # Test camera access
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print(f"✅ Camera - Accessible")
            cap.release()
        else:
            print(f"⚠️  Camera - Not accessible (check permissions/connection)")
        return True
    except ImportError:
        print(f"❌ OpenCV - Missing (install with: pip install opencv-python)")
        return False
    except Exception as e:
        print(f"⚠️  Camera test error: {e}")
        return False

def test_pyzbar():
    """Test PyZBar barcode library"""
    try:
        from pyzbar import pyzbar
        print(f"✅ PyZBar - OK")
        return True
    except ImportError:
        print(f"❌ PyZBar - Missing (install with: pip install pyzbar)")
        print(f"   On Linux/Raspberry Pi, also run: sudo apt-get install libzbar0")
        return False

def test_database():
    """Test SQLite database"""
    try:
        import sqlite3
        import os
        
        db_path = os.path.join(os.path.dirname(__file__), "cache.db")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        result = c.fetchone()
        conn.close()
        
        if result:
            print(f"✅ Database - OK (cache.db exists)")
        else:
            print(f"⚠️  Database - Empty (run cache_sync.py or scanner_app.py)")
        return True
    except Exception as e:
        print(f"❌ Database - Error: {e}")
        return False

def main():
    print("=" * 60)
    print("Smart Barcode Nutrition Scanner - System Check")
    print("=" * 60)
    print()
    
    print("Testing Python version...")
    print(f"✅ Python {sys.version.split()[0]}")
    print()
    
    print("Testing required modules...")
    results = []
    
    # Core dependencies
    results.append(test_opencv())
    results.append(test_pyzbar())
    results.append(test_import('PIL', 'Pillow'))
    results.append(test_import('requests'))
    results.append(test_import('numpy'))
    results.append(test_import('tkinter'))
    
    print()
    print("Testing database...")
    results.append(test_database())
    
    print()
    print("=" * 60)
    if all(results):
        print("✅ All tests passed! System is ready.")
        print("Run: python scanner_app.py")
    else:
        print("⚠️  Some tests failed. Please install missing dependencies.")
        print("Run: pip install -r requirements.txt")
    print("=" * 60)

if __name__ == "__main__":
    main()
