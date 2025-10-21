import cv2
from pyzbar import pyzbar
import time

def test_camera_scanning():
    print("Starting camera barcode test...")
    print("Press 'q' to quit")
    print("-" * 40)
    
    # Try to open camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Cannot open camera!")
        return
    
    print("Camera opened successfully!")
    print("Hold a barcode in front of the camera...")
    
    scan_count = 0
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("ERROR: Cannot read frame")
            break
        
        frame_count += 1
        
        # Try to detect barcodes
        barcodes = pyzbar.decode(frame)
        
        # Draw on frame and print results
        for barcode in barcodes:
            # Get barcode data
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            
            # Draw rectangle
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Put text
            text = f"{barcode_data} ({barcode_type})"
            cv2.putText(frame, text, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Print to console
            scan_count += 1
            print(f"SUCCESS! Scan #{scan_count}: {barcode_data} - Type: {barcode_type}")
        
        # Show status on frame
        status = f"Scans: {scan_count} | Frame: {frame_count}"
        cv2.putText(frame, status, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Add scanning guide
        height, width = frame.shape[:2]
        cv2.rectangle(frame, (width//4, height//4), 
                     (3*width//4, 3*height//4), (0, 255, 255), 1)
        cv2.putText(frame, "Place barcode in yellow box", 
                   (width//4, height//4 - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        # Show the frame
        cv2.imshow('Barcode Scanner Test', frame)
        
        # Every 30 frames, print status
        if frame_count % 30 == 0 and scan_count == 0:
            print(f"Scanning... (Frame {frame_count}) - No barcode detected yet")
        
        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print("-" * 40)
    print(f"Test complete! Total barcodes scanned: {scan_count}")
    if scan_count == 0:
        print("No barcodes detected. Possible issues:")
        print("1. pyzbar not installed correctly")
        print("2. Poor lighting")
        print("3. Barcode too small/far")
        print("4. Camera focus issues")

if __name__ == "__main__":
    test_camera_scanning()