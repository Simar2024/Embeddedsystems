# Tests

Testing and validation scripts for the Smart Barcode Nutrition Scanner.

## Files

### `test_setup.py`
Comprehensive system verification script that checks all dependencies and configurations.

## Running Tests

```bash
# Run from project root
python tests/test_setup.py
```

## What Gets Tested

### 1. Python Version
- ✅ Verifies Python 3.7+
- ✅ Displays current version

### 2. Required Modules
- ✅ OpenCV (opencv-python)
- ✅ PyZBar (pyzbar)
- ✅ Pillow (PIL)
- ✅ Requests
- ✅ NumPy
- ✅ Tkinter

### 3. Camera Access
- ✅ Tests camera availability
- ✅ Checks camera can be opened
- ✅ Verifies video capture functionality

### 4. Database
- ✅ Checks if cache.db exists
- ✅ Verifies products table
- ✅ Reports database status

### 5. Barcode Library
- ✅ Tests PyZBar installation
- ✅ Checks for system libzbar dependency

## Expected Output

### ✅ All Tests Passing
```
============================================================
Smart Barcode Nutrition Scanner - System Check
============================================================

Testing Python version...
✅ Python 3.11.0

Testing required modules...
✅ cv2 - OK
✅ OpenCV - OK (version 4.8.1)
✅ Camera - Accessible
✅ PyZBar - OK
✅ PIL - OK
✅ requests - OK
✅ numpy - OK
✅ tkinter - OK

Testing database...
✅ Database - OK (cache.db exists)

============================================================
✅ All tests passed! System is ready.
Run: python scanner_app.py
============================================================
```

### ⚠️ Some Tests Failing
```
============================================================
Smart Barcode Nutrition Scanner - System Check
============================================================

Testing Python version...
✅ Python 3.11.0

Testing required modules...
❌ cv2 - Missing (install with: pip install opencv-python)
✅ PyZBar - OK
...

============================================================
⚠️  Some tests failed. Please install missing dependencies.
Run: pip install -r requirements.txt
============================================================
```

## Troubleshooting

### "Camera - Not accessible"
**Windows:**
- Close other apps using the camera
- Check Windows privacy settings
- Try running as administrator

**Linux/Raspberry Pi:**
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Log out and back in

# Enable camera (RPi Camera Module)
sudo raspi-config
# Interface Options > Camera > Enable
```

### "Module Missing"
```bash
# Install all dependencies
pip install -r requirements.txt

# Or install individually
pip install opencv-python pyzbar Pillow requests numpy
```

### "libzbar not found"
**Linux/Raspberry Pi:**
```bash
sudo apt-get update
sudo apt-get install -y libzbar0 libzbar-dev
```

**Windows:**
- Install via conda: `conda install -c conda-forge zbar`
- Or download from: http://zbar.sourceforge.net/

**macOS:**
```bash
brew install zbar
```

### "Database - Empty"
```bash
# Add sample data
python scripts/add_sample_data.py

# Or sync from remote
python scripts/cache_sync.py
```

## Adding New Tests

To extend the test suite, edit `test_setup.py`:

```python
def test_new_feature():
    """Test description"""
    try:
        # Test code here
        print("✅ Feature - OK")
        return True
    except Exception as e:
        print(f"❌ Feature - Failed: {e}")
        return False

# Add to main()
results.append(test_new_feature())
```

## Continuous Integration

For automated testing, integrate with CI/CD:

```yaml
# Example GitHub Actions
name: Test Setup
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: python tests/test_setup.py
```

## Test Coverage

Current coverage:
- ✅ Dependency validation
- ✅ Hardware checks (camera)
- ✅ Database verification
- ⏭️ TODO: Unit tests for scanner_app.py
- ⏭️ TODO: Integration tests for API
- ⏭️ TODO: Barcode detection accuracy tests

## Future Tests

Planned additions:
- [ ] Unit tests for each Python module
- [ ] Integration tests for API endpoints
- [ ] Performance benchmarks
- [ ] Barcode scanning accuracy tests
- [ ] Database query performance tests
- [ ] GUI interaction tests
- [ ] Camera feed quality tests

## Manual Testing Checklist

Before deployment, manually verify:

- [ ] Camera starts successfully
- [ ] Barcodes scan correctly
- [ ] Manual entry works
- [ ] Online mode connects to backend
- [ ] Offline mode uses cache
- [ ] Allergen alerts display
- [ ] Alternatives show correctly
- [ ] GUI is responsive
- [ ] No crashes or freezes

## Reporting Issues

If tests fail unexpectedly:
1. Note the exact error message
2. Check your OS and Python version
3. Verify all dependencies installed
4. Review troubleshooting section
5. Check main README.md for solutions
6. Contact team with detailed error info

---

**Tip**: Run `test_setup.py` after every major update or system change to ensure everything still works correctly.
