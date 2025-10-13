# Frontend - Web Interface

This directory contains the web-based user interface for the Smart Barcode Nutrition Scanner.

## Files

- **`index.html`** - Standalone web interface for nutrition scanning

## Purpose

The web interface provides an alternative frontend that:
- Works in any modern web browser
- Allows manual barcode entry
- Fetches product data from PHP API
- Displays nutrition information, allergens, and alternatives
- Falls back to sample data if backend is unavailable
- Useful for testing API without Python environment

## Usage

### Local Development

1. **Option A: Direct File Access** (Limited - CORS issues)
   ```
   Simply open index.html in a browser
   ```

2. **Option B: Local Web Server** (Recommended)
   ```bash
   # Python 3
   python -m http.server 8000
   
   # Then open: http://localhost:8000/index.html
   ```

3. **Option C: Apache/Nginx**
   ```bash
   # Copy to web server directory
   sudo cp index.html /var/www/html/smartscanner/
   
   # Access: http://localhost/smartscanner/index.html
   ```

### Configuration

Update the backend URL in `index.html` (line 385):
```javascript
const backendURL = 'http://192.168.137.54/smartscanner/getProduct.php';
```

Change to your server's IP/domain.

## Features

### Current Features
- ✅ **Real-time camera barcode scanning** (QuaggaJS)
- ✅ Manual barcode input
- ✅ Product search functionality
- ✅ Nutrition information display (7 metrics)
- ✅ Allergen warnings
- ✅ Healthier alternatives suggestions
- ✅ Recent scans history
- ✅ Online/offline status indicator
- ✅ Sample data fallback
- ✅ Responsive design
- ✅ Clean black & white UI
- ✅ Audio feedback on scan
- ✅ Multiple barcode format support (EAN, UPC, Code128, Code39)

### Advanced Features
- 📸 **Browser-based camera scanning** - No Python/OpenCV needed
- 🎯 **Auto-detection** - Automatically finds and scans barcodes
- 🔊 **Audio feedback** - Beep sound on successful scan
- ⚡ **Instant results** - Automatic search after scan
- 📱 **Mobile-friendly** - Works on smartphones with camera
- ⌨️ **Keyboard shortcuts** - Press Escape to close camera

### Python App Still Better For
- ⚡ Lower latency scanning
- 💾 Local SQLite cache (full offline mode)
- 🔧 Raspberry Pi hardware integration
- 🧵 Multi-threading optimization

## Testing

### Test with Sample Barcodes
The interface includes built-in sample products:
- `1234567890` - Organic Whole Wheat Bread
- `9876543210` - Chocolate Chip Cookies

### Test with Backend
1. Ensure PHP backend is running
2. Update backend URL in HTML
3. Enter a barcode from your database
4. Verify product data displays correctly

## Deployment

### Production Deployment

1. **Update backend URL** to production server
2. **Enable HTTPS** for security
3. **Copy to web server**:
   ```bash
   sudo cp index.html /var/www/html/smartscanner/
   sudo chown www-data:www-data /var/www/html/smartscanner/index.html
   ```
4. **Configure Apache/Nginx** with proper CORS headers if needed

### CORS Configuration (Apache)

If backend is on different domain, add to `.htaccess`:
```apache
Header set Access-Control-Allow-Origin "*"
Header set Access-Control-Allow-Methods "GET, POST, OPTIONS"
Header set Access-Control-Allow-Headers "Content-Type"
```

## Mobile Compatibility

The interface is mobile-responsive and works on:
- ✅ Desktop browsers (Chrome, Firefox, Edge, Safari)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)
- ✅ Tablets (iPad, Android tablets)

## Use Cases

1. **Testing API**: Verify backend works before deploying Python app
2. **Demonstrations**: Show functionality without hardware setup
3. **Public Access**: Allow users to search products from any device
4. **Backup Interface**: Alternative if Python app is unavailable
5. **Kiosk Mode**: Deploy on touch-screen displays

## Limitations

- No local SQLite database (requires backend or uses samples)
- Limited offline functionality (no cache)
- Requires HTTPS for camera on production sites
- Camera quality depends on device

## Implemented Enhancements ✅

- [x] ~~Add QuaggaJS for browser-based barcode scanning~~ **DONE!**
- [x] ~~Real-time camera scanning~~ **DONE!**
- [x] ~~Audio feedback on scan~~ **DONE!**
- [x] ~~Multiple barcode format support~~ **DONE!**

## Future Enhancements

Potential improvements:
- [ ] Implement Service Worker for offline support
- [ ] Add PWA (Progressive Web App) features
- [ ] Include nutritional graphs/charts
- [ ] Add user accounts and saved products
- [ ] Implement product comparison feature
- [ ] Add barcode history/analytics
- [ ] QR code scanning support

## Support

For web-specific issues:
- Check browser console for errors
- Verify backend URL is correct and accessible
- Ensure CORS is properly configured
- Test with sample barcodes first

For general project support, see main [README.md](../README.md)
