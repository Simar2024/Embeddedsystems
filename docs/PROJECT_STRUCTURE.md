# Project Structure

## Directory Layout

```
Embeddedsystems/
├── scanner_app.py              # Main GUI application (run this)
├── requirements.txt            # Python dependencies
├── cache.db                    # Local SQLite database (auto-generated)
├── README.md                   # Main documentation
├── .gitignore                  # Git ignore rules
│
├── backend/                    # PHP API Backend
│   ├── README.md              # Backend setup guide
│   ├── getProduct.php         # Single product lookup endpoint
│   ├── getAllProducts.php     # Bulk product retrieval endpoint
│   └── test.php               # API test file
│
├── frontend/                   # Web Interface (Alternative UI)
│   └── index.html             # Web-based scanner interface
│
├── scripts/                    # Utility Scripts
│   ├── README.md              # Scripts documentation
│   ├── cache_sync.py          # Sync remote DB to local cache
│   └── add_sample_data.py     # Add test products to database
│
├── tests/                      # Testing & Validation
│   └── test_setup.py          # System setup verification
│
└── docs/                       # Documentation
    ├── QUICKSTART.md          # Quick start guide
    └── PROJECT_STRUCTURE.md   # This file
```

## File Descriptions

### Root Directory

#### `scanner_app.py` ⭐ MAIN APPLICATION
- **Purpose**: Primary GUI application with camera integration
- **Run**: `python scanner_app.py`
- **Features**:
  - Real-time barcode scanning with camera
  - Manual barcode entry
  - Nutrition information display
  - Allergen alerts
  - Offline/online database support
  - Multithreaded camera processing

#### `requirements.txt`
- **Purpose**: Lists all Python dependencies
- **Install**: `pip install -r requirements.txt`
- **Dependencies**:
  - opencv-python (camera & vision)
  - pyzbar (barcode decoding)
  - Pillow (image handling)
  - requests (HTTP API calls)
  - numpy (numerical operations)

#### `cache.db` (Auto-generated)
- **Purpose**: Local SQLite database for offline support
- **Created by**: Running any script or the main app
- **Contains**: Cached product nutrition data
- **Note**: Gitignored, not committed to repository

---

### `/backend/` - PHP API

#### Purpose
Provides RESTful API endpoints for product data retrieval from MySQL database.

#### Files
- **`getProduct.php`**: Returns single product by barcode
- **`getAllProducts.php`**: Returns all products for cache sync
- **`test.php`**: Simple connectivity test

#### Setup
1. Install LAMP stack (Linux, Apache, MySQL, PHP)
2. Create MySQL database and user
3. Deploy PHP files to web server
4. Update database credentials in PHP files

#### Deployment Location
- Linux/RPi: `/var/www/html/smartscanner/`
- Local: XAMPP/WAMP `htdocs/smartscanner/`

---

### `/frontend/` - Web Interface

#### `index.html`
- **Purpose**: Alternative web-based interface
- **Features**:
  - Manual barcode input
  - Fetches from PHP API
  - Displays nutrition info
  - Sample data fallback
- **Use Case**: Testing API without running Python app
- **Access**: `http://localhost/smartscanner/index.html`

---

### `/scripts/` - Utilities

#### `cache_sync.py`
- **Purpose**: Synchronize remote MySQL to local SQLite
- **Run**: `python scripts/cache_sync.py`
- **When to use**:
  - After adding products to remote database
  - Before going offline
  - Periodic updates

#### `add_sample_data.py`
- **Purpose**: Add 10 test products to local database
- **Run**: `python scripts/add_sample_data.py`
- **When to use**:
  - Initial setup and testing
  - Development without backend
  - Demonstrations

---

### `/tests/` - Testing

#### `test_setup.py`
- **Purpose**: Verify system dependencies and configuration
- **Run**: `python tests/test_setup.py`
- **Checks**:
  - Python version
  - Required modules installed
  - Camera accessibility
  - Database status
- **When to use**: After installation, before first run

---

### `/docs/` - Documentation

#### `QUICKSTART.md`
- Quick reference for installation and first run
- Platform-specific instructions (Windows/RPi)
- Common troubleshooting

#### `PROJECT_STRUCTURE.md`
- This file
- Detailed project organization
- File purposes and relationships

---

## Data Flow

```
┌─────────────────┐
│  scanner_app.py │  ←─── Main Application
└────────┬────────┘
         │
         ├─→ Camera (OpenCV) ──→ Barcode Detection (PyZBar)
         │
         ├─→ Remote Database (PHP API + MySQL)
         │   └─→ backend/getProduct.php
         │
         └─→ Local Cache (SQLite)
             └─→ cache.db
                 ├─ Updated by: scripts/cache_sync.py
                 └─ Tested with: scripts/add_sample_data.py
```

## Workflow

### First-Time Setup
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Test setup**: `python tests/test_setup.py`
3. **Add sample data**: `python scripts/add_sample_data.py`
4. **Run application**: `python scanner_app.py`

### With Backend (Production)
1. **Setup backend**: Follow `backend/README.md`
2. **Add products**: Insert into MySQL database
3. **Sync cache**: `python scripts/cache_sync.py`
4. **Run application**: `python scanner_app.py`

### Development Workflow
1. **Test changes**: Use sample data
2. **Update docs**: Keep documentation current
3. **Test both modes**: Online and offline
4. **Commit changes**: Git workflow

---

## Configuration Files

### Application Config
- **Backend URL**: Line 19 in `scanner_app.py`
  ```python
  self.backend_url = "http://localhost/smartscanner/getProduct.php"
  ```

### Database Config
- **PHP credentials**: In `backend/*.php` files
  ```php
  $servername = "localhost";
  $username = "smartuser";
  $password = "password123";
  $dbname = "smartscanner";
  ```

---

## Git Management

### `.gitignore` Excludes
- `cache.db` - Local database
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python
- `.vscode/`, `.idea/` - IDE files
- Virtual environments

### What to Commit
- ✅ Source code (`.py`, `.php`, `.html`)
- ✅ Documentation (`.md`)
- ✅ Configuration templates
- ✅ Requirements file
- ❌ Database files
- ❌ IDE settings
- ❌ Cache files

---

## Adding New Features

### New Nutrition Field
1. Update database schema in `scripts/cache_sync.py`
2. Update backend PHP queries
3. Update `scanner_app.py` display logic
4. Update sample data in `scripts/add_sample_data.py`

### New API Endpoint
1. Create PHP file in `backend/`
2. Update `backend/README.md`
3. Add corresponding function in `scanner_app.py`
4. Test with `tests/test_setup.py`

### New UI Feature
1. Modify `scanner_app.py` GUI code
2. Test with sample data
3. Update screenshots/docs if needed

---

## Maintenance

### Regular Tasks
- **Weekly**: Sync cache with `cache_sync.py`
- **Monthly**: Update dependencies `pip install -U -r requirements.txt`
- **As needed**: Add new products to database

### Backup
- **Database**: Backup `cache.db` and MySQL database
- **Code**: Git commits and remote repository
- **Docs**: Keep documentation updated

---

## Team Collaboration

- **Simarpreet Singh**: 21153978
- **Param Patel**: 20128905
- **Allister Mcgregor**: 21154675

### Workflow
1. Pull latest changes
2. Create feature branch
3. Make changes and test
4. Update documentation
5. Commit and push
6. Create pull request

---

This structure follows best practices for embedded systems projects:
- ✅ Separation of concerns (backend/frontend/scripts)
- ✅ Clear documentation
- ✅ Easy testing and deployment
- ✅ Scalable and maintainable
- ✅ Version control friendly
