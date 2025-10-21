import cv2
from pyzbar import pyzbar

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera not working!")
        break
    
    barcodes = pyzbar.decode(frame)
    for barcode in barcodes:
        print(f"Found: {barcode.data.decode('utf-8')}")
    
    cv2.imshow('Barcode Test', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()