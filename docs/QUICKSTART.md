# Quick Start Guide 🚀

## For Windows (Development/Testing)

### 1. Install Dependencies
```powershell
# Install Python packages
pip install opencv-python Pillow pyzbar requests numpy

# Note: You may need to install Visual C++ redistributable for OpenCV
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### 2. Install ZBar (for barcode decoding)
- Download ZBar for Windows from: http://zbar.sourceforge.net/
- Or install via conda: `conda install -c conda-forge zbar`

### 3. Run Test
```powershell
python test_setup.py
```

### 4. Run Application
```powershell
python scanner_app.py
```

---

## For Raspberry Pi (Production)

### 1. System Setup
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y python3-opencv python3-pil python3-pil.imagetk python3-tk
sudo apt-get install -y libzbar0 libzbar-dev
sudo apt-get install -y python3-pip
```

### 2. Install Python Packages
```bash
pip3 install -r requirements.txt
```

### 3. Enable Camera (if using Pi Camera)
```bash
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable
# Reboot: sudo reboot
```

### 4. Test Setup
```bash
python3 test_setup.py
```

### 5. Sync Database Cache
```bash
python3 cache_sync.py
```

### 6. Run Application
```bash
python3 scanner_app.py
```

---

## Testing Without Hardware

If you don't have a camera or barcode scanner yet:

1. **Use Manual Entry**: The app allows typing barcodes directly
2. **Test Barcodes**:
   - `1234567890` - Sample product 1
   - `9876543210` - Sample product 2
3. **Print Test Barcodes**: Search online for "test barcode images" and display on phone/screen

---

## Common Issues

### "No module named cv2"
```bash
pip install opencv-python
```

### "No module named pyzbar"
```bash
pip install pyzbar
# On Linux/Pi: sudo apt-get install libzbar0
```

### "Cannot open camera"
- **Windows**: Check if another app is using the camera
- **Linux/Pi**: Add user to video group: `sudo usermod -a -G video $USER`
- **Permissions**: Run with sudo (not recommended) or fix permissions

### "Backend not reachable"
- The app works offline with cached data
- To enable remote database, set up LAMP stack and PHP backend
- Update backend URL in `scanner_app.py` line 19

---

## Next Steps

1. ✅ Test with sample barcodes
2. ✅ Set up remote database (optional)
3. ✅ Add your own products to database
4. ✅ Test with real barcodes
5. ✅ Deploy on Raspberry Pi

---

**Need Help?** Check the full README.md for detailed documentation.
