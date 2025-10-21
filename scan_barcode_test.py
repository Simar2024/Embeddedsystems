import cv2
from pyzbar import pyzbar

# Test with a simple image
img_path = "test_barcode.jpg"  # Put a barcode image here
image = cv2.imread(img_path)

if image is None:
    print("Image not found!")
else:
    # Try detection
    barcodes = pyzbar.decode(image)
    
    if barcodes:
        for barcode in barcodes:
            print(f"Found: {barcode.data.decode('utf-8')}")
    else:
        print("No barcode found - pyzbar might not be installed correctly")
        
        # Try grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        barcodes = pyzbar.decode(gray)
        if barcodes:
            print("Found in grayscale!")
        else:
            print("Still nothing - check pyzbar installation")