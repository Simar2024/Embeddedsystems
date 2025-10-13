# Scripts

Utility scripts for database management and testing.

## Files

### `cache_sync.py`
Synchronizes the remote MySQL database to the local SQLite cache.

**Usage:**
```bash
python scripts/cache_sync.py
```

**What it does:**
- Fetches all products from remote PHP API
- Updates local SQLite cache
- Handles offline mode gracefully
- Creates database schema if needed

**Run this:**
- After adding products to remote database
- Before using the scanner offline
- Periodically to keep cache updated

---

### `add_sample_data.py`
Adds sample test products to the local database.

**Usage:**
```bash
python scripts/add_sample_data.py
```

**What it does:**
- Creates 10 sample products with complete nutrition data
- Adds test barcodes for immediate testing
- Useful for development and demos

**Sample Products:**
- `1234567890` - Organic Whole Wheat Bread
- `9876543210` - Chocolate Chip Cookies
- `5551234567` - Greek Yogurt
- `7778889999` - Potato Chips
- `1112223334` - Almond Milk
- And more...

---

## Running Scripts from Root Directory

```bash
# From project root
python scripts/cache_sync.py
python scripts/add_sample_data.py
```

## Important Notes

- Scripts create `cache.db` in the **project root** directory
- Both scripts will create the database schema if it doesn't exist
- `cache_sync.py` requires network access to remote API
- `add_sample_data.py` works completely offline
