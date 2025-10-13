#!/usr/bin/env python3
"""
Smart Barcode Nutrition Scanner
Main Application with Camera Integration
Authors: Simarpreet Singh, Param Patel
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk
import threading
import queue
import requests
import sqlite3
import json
import os
from datetime import datetime
from pyzbar.pyzbar import decode
import time

class BarcodeScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Barcode Nutrition Scanner")
        self.root.geometry("1000x700")
        self.root.configure(bg="#ffffff")
        
        # Configuration
        self.backend_url = "http://localhost/smartscanner/getProduct.php"
        self.db_path = os.path.join(os.path.dirname(__file__), "cache.db")
        
        # State variables
        self.camera_running = False
        self.video_capture = None
        self.last_scanned_barcode = None
        self.last_scan_time = 0
        self.scan_cooldown = 2  # seconds between scans
        self.frame_queue = queue.Queue(maxsize=2)
        
        # Initialize database
        self.init_database()
        
        # Build UI
        self.build_ui()
        
        # Start camera by default
        self.toggle_camera()
        
    def init_database(self):
        """Initialize local SQLite cache"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
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
        conn.commit()
        conn.close()
        
    def build_ui(self):
        """Build the main user interface"""
        # Header
        header_frame = tk.Frame(self.root, bg="#000000", height=80)
        header_frame.pack(fill=tk.X, padx=0, pady=0)
        
        title_label = tk.Label(
            header_frame, 
            text="🔍 Smart Barcode Nutrition Scanner",
            font=("Arial", 24, "bold"),
            bg="#000000",
            fg="#ffffff"
        )
        title_label.pack(pady=20)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#f8f9fa", height=40)
        status_frame.pack(fill=tk.X, padx=0, pady=0)
        
        self.status_label = tk.Label(
            status_frame,
            text="● Online - Connected to Database",
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#28a745"
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.last_update_label = tk.Label(
            status_frame,
            text="Last scan: Never",
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#6c757d"
        )
        self.last_update_label.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # Main content area - split into two panels
        main_frame = tk.Frame(self.root, bg="#ffffff")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Camera and controls
        left_frame = tk.Frame(main_frame, bg="#ffffff")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Camera view
        camera_label = tk.Label(left_frame, text="Camera View", font=("Arial", 14, "bold"), bg="#ffffff")
        camera_label.pack(pady=(0, 10))
        
        self.camera_frame = tk.Label(
            left_frame, 
            bg="#000000",
            width=480,
            height=360,
            text="Camera initializing...",
            font=("Arial", 12),
            fg="#ffffff"
        )
        self.camera_frame.pack(pady=10)
        
        # Camera controls
        controls_frame = tk.Frame(left_frame, bg="#ffffff")
        controls_frame.pack(pady=10)
        
        self.camera_btn = tk.Button(
            controls_frame,
            text="📷 Stop Camera",
            font=("Arial", 12, "bold"),
            bg="#000000",
            fg="#ffffff",
            padx=20,
            pady=10,
            border=0,
            cursor="hand2",
            command=self.toggle_camera
        )
        self.camera_btn.pack(side=tk.LEFT, padx=5)
        
        # Manual input
        input_frame = tk.Frame(left_frame, bg="#ffffff")
        input_frame.pack(pady=20, fill=tk.X)
        
        manual_label = tk.Label(input_frame, text="Manual Barcode Entry:", font=("Arial", 12), bg="#ffffff")
        manual_label.pack(anchor=tk.W)
        
        input_row = tk.Frame(input_frame, bg="#ffffff")
        input_row.pack(fill=tk.X, pady=10)
        
        self.barcode_entry = tk.Entry(
            input_row,
            font=("Arial", 14),
            bd=2,
            relief=tk.SOLID
        )
        self.barcode_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.barcode_entry.bind('<Return>', lambda e: self.manual_search())
        
        search_btn = tk.Button(
            input_row,
            text="Search",
            font=("Arial", 12, "bold"),
            bg="#000000",
            fg="#ffffff",
            padx=20,
            pady=5,
            border=0,
            cursor="hand2",
            command=self.manual_search
        )
        search_btn.pack(side=tk.LEFT)
        
        # Right panel - Results
        right_frame = tk.Frame(main_frame, bg="#ffffff", width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        results_label = tk.Label(right_frame, text="Scan Results", font=("Arial", 14, "bold"), bg="#ffffff")
        results_label.pack(pady=(0, 10))
        
        # Scrollable results area
        results_container = tk.Frame(right_frame, bg="#ffffff")
        results_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(results_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_canvas = tk.Canvas(
            results_container,
            bg="#ffffff",
            yscrollcommand=scrollbar.set,
            highlightthickness=0
        )
        self.results_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.results_canvas.yview)
        
        self.results_frame = tk.Frame(self.results_canvas, bg="#ffffff")
        self.results_canvas.create_window((0, 0), window=self.results_frame, anchor=tk.NW)
        
        # Empty state
        self.show_empty_state()
        
        # Update scroll region
        self.results_frame.bind("<Configure>", lambda e: self.results_canvas.configure(
            scrollregion=self.results_canvas.bbox("all")
        ))
        
    def show_empty_state(self):
        """Show empty state when no scans yet"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        empty_label = tk.Label(
            self.results_frame,
            text="📦\n\nNo products scanned yet\n\nScan a barcode or enter manually",
            font=("Arial", 12),
            bg="#ffffff",
            fg="#6c757d",
            justify=tk.CENTER
        )
        empty_label.pack(pady=50)
        
    def toggle_camera(self):
        """Toggle camera on/off"""
        if self.camera_running:
            self.stop_camera()
        else:
            self.start_camera()
            
    def start_camera(self):
        """Start the camera feed"""
        if self.camera_running:
            return
            
        try:
            # Try different camera indices
            for camera_index in [0, 1, 2]:
                self.video_capture = cv2.VideoCapture(camera_index)
                if self.video_capture.isOpened():
                    break
                    
            if not self.video_capture.isOpened():
                messagebox.showerror("Camera Error", "Could not access camera. Please check connection.")
                return
                
            self.camera_running = True
            self.camera_btn.config(text="📷 Stop Camera")
            
            # Start camera thread
            self.camera_thread = threading.Thread(target=self.camera_loop, daemon=True)
            self.camera_thread.start()
            
            # Start UI update thread
            self.root.after(10, self.update_camera_frame)
            
        except Exception as e:
            messagebox.showerror("Camera Error", f"Failed to start camera: {str(e)}")
            
    def stop_camera(self):
        """Stop the camera feed"""
        self.camera_running = False
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        self.camera_btn.config(text="📷 Start Camera")
        self.camera_frame.config(image="", text="Camera stopped", bg="#000000", fg="#ffffff")
        
    def camera_loop(self):
        """Main camera loop running in separate thread"""
        while self.camera_running:
            if self.video_capture and self.video_capture.isOpened():
                ret, frame = self.video_capture.read()
                if ret:
                    # Decode barcodes
                    current_time = time.time()
                    if current_time - self.last_scan_time > self.scan_cooldown:
                        barcodes = decode(frame)
                        if barcodes:
                            for barcode in barcodes:
                                barcode_data = barcode.data.decode('utf-8')
                                if barcode_data != self.last_scanned_barcode:
                                    self.last_scanned_barcode = barcode_data
                                    self.last_scan_time = current_time
                                    # Trigger product lookup in main thread
                                    self.root.after(0, self.lookup_product, barcode_data)
                                    
                                # Draw rectangle around barcode
                                points = barcode.polygon
                                if len(points) == 4:
                                    pts = [(point.x, point.y) for point in points]
                                    cv2.polylines(frame, [np.array(pts, dtype=np.int32)], True, (0, 255, 0), 3)
                                    
                                # Display barcode text
                                x, y = barcode.rect.left, barcode.rect.top
                                cv2.putText(frame, barcode_data, (x, y - 10), 
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                    # Add to queue for display
                    if not self.frame_queue.full():
                        try:
                            self.frame_queue.put_nowait(frame)
                        except queue.Full:
                            pass
                            
            time.sleep(0.03)  # ~30 FPS
            
    def update_camera_frame(self):
        """Update the camera display in the UI"""
        if self.camera_running:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get_nowait()
                    
                    # Resize frame to fit display
                    frame = cv2.resize(frame, (480, 360))
                    
                    # Convert to RGB for Tkinter
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    self.camera_frame.imgtk = imgtk
                    self.camera_frame.configure(image=imgtk, text="", bg="#000000")
                    
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Error updating frame: {e}")
                
            # Schedule next update
            self.root.after(30, self.update_camera_frame)
            
    def manual_search(self):
        """Handle manual barcode entry"""
        barcode = self.barcode_entry.get().strip()
        if barcode:
            self.lookup_product(barcode)
            self.barcode_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Required", "Please enter a barcode number")
            
    def lookup_product(self, barcode):
        """Look up product information by barcode"""
        # Run in separate thread to avoid blocking UI
        thread = threading.Thread(target=self._lookup_product_thread, args=(barcode,), daemon=True)
        thread.start()
        
    def _lookup_product_thread(self, barcode):
        """Product lookup in separate thread"""
        try:
            # Try remote database first
            response = requests.get(f"{self.backend_url}?barcode={barcode}", timeout=3)
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data and data:
                    # Update cache
                    self.update_cache(data)
                    # Display results
                    self.root.after(0, self.display_product, data, "online")
                    return
        except Exception as e:
            print(f"Remote lookup failed: {e}")
            
        # Fall back to local cache
        product = self.get_from_cache(barcode)
        if product:
            self.root.after(0, self.display_product, product, "offline")
        else:
            self.root.after(0, messagebox.showwarning, "Product Not Found", 
                          f"Barcode {barcode} not found in database or cache.")
            
    def get_from_cache(self, barcode):
        """Retrieve product from local cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM products WHERE barcode=?", (barcode,))
            row = c.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"Cache lookup error: {e}")
            return None
            
    def update_cache(self, product):
        """Update local cache with product data"""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
            INSERT OR REPLACE INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                product.get('barcode'),
                product.get('name'),
                product.get('calories'),
                product.get('fat'),
                product.get('protein'),
                product.get('carbs'),
                product.get('allergens'),
                product.get('healthier_alternative'),
                product.get('fiber', 0),
                product.get('sugar', 0),
                product.get('sodium', 0)
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Cache update error: {e}")
            
    def display_product(self, product, source):
        """Display product information in the results panel"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        # Update status
        status_text = "● Online" if source == "online" else "○ Offline (Cached)"
        status_color = "#28a745" if source == "online" else "#ffc107"
        self.status_label.config(text=status_text, fg=status_color)
        self.last_update_label.config(text=f"Last scan: {datetime.now().strftime('%H:%M:%S')}")
        
        # Product card
        card = tk.Frame(self.results_frame, bg="#ffffff", relief=tk.SOLID, bd=2)
        card.pack(fill=tk.X, pady=10, padx=10)
        
        # Product header
        header = tk.Frame(card, bg="#ffffff")
        header.pack(fill=tk.X, padx=15, pady=15)
        
        name_label = tk.Label(
            header,
            text=product.get('name', 'Unknown Product'),
            font=("Arial", 16, "bold"),
            bg="#ffffff",
            fg="#000000",
            wraplength=300,
            justify=tk.LEFT
        )
        name_label.pack(anchor=tk.W)
        
        barcode_label = tk.Label(
            header,
            text=f"Barcode: {product.get('barcode', 'N/A')}",
            font=("Courier", 10),
            bg="#f8f9fa",
            fg="#000000",
            padx=10,
            pady=5,
            relief=tk.SOLID,
            bd=1
        )
        barcode_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Allergen alert
        allergens = product.get('allergens', '')
        if allergens and allergens != 'None':
            allergen_frame = tk.Frame(card, bg="#fff3cd", relief=tk.SOLID, bd=2)
            allergen_frame.pack(fill=tk.X, padx=15, pady=10)
            
            allergen_label = tk.Label(
                allergen_frame,
                text=f"⚠️ Allergen Alert: Contains {allergens}",
                font=("Arial", 11, "bold"),
                bg="#fff3cd",
                fg="#856404",
                padx=10,
                pady=10
            )
            allergen_label.pack()
            
        # Nutrition grid
        nutrition_frame = tk.Frame(card, bg="#ffffff")
        nutrition_frame.pack(fill=tk.X, padx=15, pady=10)
        
        nutrients = [
            ('Calories', product.get('calories', 0), 'kcal'),
            ('Protein', product.get('protein', 0), 'g'),
            ('Carbs', product.get('carbs', 0), 'g'),
            ('Fat', product.get('fat', 0), 'g'),
            ('Fiber', product.get('fiber', 0), 'g'),
            ('Sugar', product.get('sugar', 0), 'g'),
            ('Sodium', product.get('sodium', 0), 'mg')
        ]
        
        for i, (label, value, unit) in enumerate(nutrients):
            row = i // 3
            col = i % 3
            
            nutrient_box = tk.Frame(nutrition_frame, bg="#f8f9fa", relief=tk.SOLID, bd=1)
            nutrient_box.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            tk.Label(
                nutrient_box,
                text=label,
                font=("Arial", 9),
                bg="#f8f9fa",
                fg="#6c757d"
            ).pack(pady=(10, 0))
            
            tk.Label(
                nutrient_box,
                text=f"{value}",
                font=("Arial", 18, "bold"),
                bg="#f8f9fa",
                fg="#000000"
            ).pack()
            
            tk.Label(
                nutrient_box,
                text=unit,
                font=("Arial", 8),
                bg="#f8f9fa",
                fg="#6c757d"
            ).pack(pady=(0, 10))
            
        # Configure grid weights
        for i in range(3):
            nutrition_frame.grid_columnconfigure(i, weight=1)
            
        # Healthier alternatives
        alternative = product.get('healthier_alternative', '')
        if alternative and alternative != 'None':
            alt_frame = tk.Frame(card, bg="#d4edda", relief=tk.SOLID, bd=2)
            alt_frame.pack(fill=tk.X, padx=15, pady=10)
            
            tk.Label(
                alt_frame,
                text="💡 Healthier Alternative",
                font=("Arial", 12, "bold"),
                bg="#d4edda",
                fg="#155724"
            ).pack(anchor=tk.W, padx=10, pady=(10, 5))
            
            tk.Label(
                alt_frame,
                text=alternative,
                font=("Arial", 11),
                bg="#d4edda",
                fg="#155724"
            ).pack(anchor=tk.W, padx=10, pady=(0, 10))
            
    def on_closing(self):
        """Clean up when closing the application"""
        self.stop_camera()
        self.root.destroy()

def main():
    """Main entry point"""
    # Import numpy here to avoid issues if not installed
    global np
    import numpy as np
    
    root = tk.Tk()
    app = BarcodeScannerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
