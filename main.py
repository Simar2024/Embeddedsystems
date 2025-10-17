"""
Smart Barcode Nutrition Scanner
Main Application - Raspberry Pi with SenseHat + Joystick
Python 3.7+

Run: python3 main.py
Exit Fullscreen: Press ESC or F11
Joystick: UP/DOWN to navigate, MIDDLE to select
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from pyzbar import pyzbar
import requests
import sqlite3
import threading
import json
from datetime import datetime
from PIL import Image, ImageTk
import os
import sys

# Try to import SenseHat (only works on Raspberry Pi)
try:
    from sense_hat import SenseHat
    SENSEHAT_AVAILABLE = True
    sense = SenseHat()
    sense.clear()
except ImportError:
    SENSEHAT_AVAILABLE = False
    print("⚠️  SenseHat not available - LED features disabled (running on non-RPi?)")

# Configuration
API_BASE_URL = "http://localhost/api"  # Change if API is hosted elsewhere
SQLITE_DB = "nutrition_cache.db"

# LED Colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
OFF = (0, 0, 0)

class NutritionScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Barcode Nutrition Scanner")
        
        # Make fullscreen for Raspberry Pi display
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg="#f0f0f0")
        
        # Bind keys
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>', lambda e: self.root.attributes('-fullscreen', True))
        self.root.bind('<q>', lambda e: self.quit_app())
        
        # Initialize database
        self.init_sqlite_db()
        
        # Variables
        self.is_online = self.check_connection()
        self.scanning = False
        self.camera = None
        self.user_allergens = self.load_user_allergens()
        self.led_thread = None
        
        # Joystick variables
        self.joystick_thread = None
        self.joystick_running = False
        self.current_menu_index = 0
        self.menu_items = []
        
        # Create GUI
        self.create_gui()
        
        # Start joystick listener
        if SENSEHAT_AVAILABLE:
            self.start_joystick_listener()
        
        print("✅ Application started successfully")
        if SENSEHAT_AVAILABLE:
            print("✅ SenseHat LED matrix ready")
            print("✅ Joystick navigation enabled - UP/DOWN to navigate, MIDDLE to select")
        
    def init_sqlite_db(self):
        """Initialize SQLite database for offline cache"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                brand TEXT,
                category TEXT,
                calories INTEGER,
                protein REAL,
                carbs REAL,
                sugar REAL,
                fats REAL,
                saturated_fats REAL,
                fiber REAL,
                sodium REAL,
                allergens TEXT,
                health_score INTEGER,
                is_healthy INTEGER,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT NOT NULL,
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                preference_key TEXT UNIQUE NOT NULL,
                preference_value TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ SQLite database initialized")
        
    def load_user_allergens(self):
        """Load user's allergen preferences"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute("SELECT preference_value FROM user_preferences WHERE preference_key='allergens'")
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0]:
            return set(row[0].split(','))
        return set()
        
    def save_user_allergens(self, allergens):
        """Save user's allergen preferences"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        allergen_str = ','.join(allergens)
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (preference_key, preference_value)
            VALUES ('allergens', ?)
        ''', (allergen_str,))
        
        conn.commit()
        conn.close()
        self.user_allergens = allergens
        
    def check_connection(self):
        """Check if we have internet connection to API"""
        try:
            response = requests.get(f"{API_BASE_URL}/test_connection.php", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def set_led_color(self, color, pattern='solid'):
        """Set SenseHat LED color"""
        if not SENSEHAT_AVAILABLE:
            return
            
        if pattern == 'solid':
            sense.clear(color)
        elif pattern == 'flash':
            # Flash pattern in separate thread
            if self.led_thread and self.led_thread.is_alive():
                return
            self.led_thread = threading.Thread(target=self._flash_led, args=(color,), daemon=True)
            self.led_thread.start()
    
    def _flash_led(self, color):
        """Flash LED pattern"""
        for _ in range(6):
            sense.clear(color)
            threading.Event().wait(0.3)
            sense.clear()
            threading.Event().wait(0.3)
        sense.clear(color)
    
    def start_joystick_listener(self):
        """Start listening to joystick events"""
        if not SENSEHAT_AVAILABLE:
            return
        
        self.joystick_running = True
        self.joystick_thread = threading.Thread(target=self._joystick_loop, daemon=True)
        self.joystick_thread.start()
        
    def _joystick_loop(self):
        """Joystick event loop - runs in separate thread"""
        while self.joystick_running:
            for event in sense.stick.get_events():
                if event.action == "pressed":
                    if event.direction == "up":
                        self.joystick_up()
                    elif event.direction == "down":
                        self.joystick_down()
                    elif event.direction == "middle":
                        self.joystick_select()
                    elif event.direction == "left":
                        self.refresh_connection()
                    elif event.direction == "right":
                        self.open_settings()
            threading.Event().wait(0.1)
    
    def joystick_up(self):
        """Handle joystick UP - navigate menu"""
        if len(self.menu_items) > 0:
            self.current_menu_index = (self.current_menu_index - 1) % len(self.menu_items)
            self.highlight_menu_item()
            self.set_led_color(BLUE, 'solid')
    
    def joystick_down(self):
        """Handle joystick DOWN - navigate menu"""
        if len(self.menu_items) > 0:
            self.current_menu_index = (self.current_menu_index + 1) % len(self.menu_items)
            self.highlight_menu_item()
            self.set_led_color(BLUE, 'solid')
    
    def joystick_select(self):
        """Handle joystick MIDDLE - select current menu item"""
        if len(self.menu_items) > 0:
            selected_button = self.menu_items[self.current_menu_index]
            # Invoke button in main thread
            self.root.after(0, selected_button.invoke)
            self.set_led_color(GREEN, 'solid')
    
    def highlight_menu_item(self):
        """Highlight current menu item"""
        for i, btn in enumerate(self.menu_items):
            if i == self.current_menu_index:
                btn.configure(relief=tk.RAISED, borderwidth=4)
            else:
                btn.configure(relief=tk.FLAT, borderwidth=1)
    
    def quit_app(self):
        """Quit application and cleanup"""
        self.joystick_running = False
        if SENSEHAT_AVAILABLE:
            sense.clear()
        self.root.quit()
    
    def create_gui(self):
        """Create the main GUI interface"""
        # Title bar
        title_frame = tk.Frame(self.root, bg="#4a90e2", height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="🔍 Smart Nutrition Scanner",
            font=("Arial", 20, "bold"),
            bg="#4a90e2",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        if SENSEHAT_AVAILABLE:
            joystick_label = tk.Label(
                title_frame,
                text="🕹️ Joystick: ↑↓ Navigate • ⏺ Select • ← Refresh • → Settings",
                font=("Arial", 10),
                bg="#4a90e2",
                fg="white"
            )
            joystick_label.pack(side=tk.LEFT, padx=10, pady=15)
        
        exit_btn = tk.Button(
            title_frame,
            text="✕ EXIT",
            command=self.quit_app,
            bg="#f44336",
            fg="white",
            font=("Arial", 14, "bold"),
            width=6,
            relief=tk.FLAT
        )
        exit_btn.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Status bar
        status_frame = tk.Frame(self.root, bg="#e8e8e8", height=50)
        status_frame.pack(fill=tk.X)
        
        status_color = "#4caf50" if self.is_online else "#ff9800"
        status_text = "🟢 ONLINE" if self.is_online else "🟠 OFFLINE"
        
        self.status_label = tk.Label(
            status_frame,
            text=status_text,
            font=("Arial", 12, "bold"),
            bg="#e8e8e8",
            fg=status_color
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        allergen_count = len(self.user_allergens)
        allergen_text = f"⚠️ {allergen_count} Allergen(s) Set" if allergen_count > 0 else "No Allergens Set"
        self.allergen_status_label = tk.Label(
            status_frame,
            text=allergen_text,
            font=("Arial", 11),
            bg="#e8e8e8",
            fg="#f44336" if allergen_count > 0 else "#666"
        )
        self.allergen_status_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        if SENSEHAT_AVAILABLE:
            led_status = tk.Label(
                status_frame,
                text="💡 LED Ready | 🕹️ Joystick Active",
                font=("Arial", 11),
                bg="#e8e8e8",
                fg="#4caf50"
            )
            led_status.pack(side=tk.LEFT, padx=20, pady=10)
        
        settings_btn = tk.Button(
            status_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            bg="#9c27b0",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        settings_btn.pack(side=tk.RIGHT, padx=20, pady=10)
        
        refresh_btn = tk.Button(
            status_frame,
            text="🔄 Refresh",
            command=self.refresh_connection,
            bg="#2196f3",
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=8
        )
        refresh_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Main content
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel - Scanning
        left_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        scan_title = tk.Label(
            left_frame,
            text="📷 Scan Area",
            font=("Arial", 14, "bold"),
            bg="white"
        )
        scan_title.pack(pady=10)
        
        self.camera_label = tk.Label(left_frame, bg="black", text="Camera Off", fg="white", font=("Arial", 16))
        self.camera_label.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Buttons
        btn_frame = tk.Frame(left_frame, bg="white")
        btn_frame.pack(pady=15)
        
        self.start_camera_btn = tk.Button(
            btn_frame,
            text="📹 Start\nCamera",
            command=self.start_camera_scan,
            bg="#4caf50",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3
        )
        self.start_camera_btn.grid(row=0, column=0, padx=5)
        self.menu_items.append(self.start_camera_btn)
        
        self.stop_camera_btn = tk.Button(
            btn_frame,
            text="⏹ Stop\nCamera",
            command=self.stop_camera_scan,
            bg="#f44336",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3,
            state=tk.DISABLED
        )
        self.stop_camera_btn.grid(row=0, column=1, padx=5)
        
        upload_btn = tk.Button(
            btn_frame,
            text="📁 Upload\nImage",
            command=self.upload_image,
            bg="#2196f3",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3
        )
        upload_btn.grid(row=1, column=0, padx=5, pady=5)
        self.menu_items.append(upload_btn)
        
        manual_btn = tk.Button(
            btn_frame,
            text="⌨️ Manual\nEntry",
            command=self.manual_entry,
            bg="#ff9800",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3
        )
        manual_btn.grid(row=1, column=1, padx=5, pady=5)
        self.menu_items.append(manual_btn)
        
        # Right panel - Results
        right_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        results_title = tk.Label(
            right_frame,
            text="📊 Nutrition Information",
            font=("Arial", 14, "bold"),
            bg="white"
        )
        results_title.pack(pady=10)
        
        # Scrollable results
        canvas = tk.Canvas(right_frame, bg="white")
        scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
        self.results_frame = tk.Frame(canvas, bg="white")
        
        self.results_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        self.show_welcome_message()
        
        # Highlight first menu item
        if self.menu_items:
            self.highlight_menu_item()
        
    def open_settings(self):
        """Open allergen settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ Settings")
        settings_window.geometry("500x600")
        settings_window.configure(bg="white")
        
        tk.Label(
            settings_window,
            text="⚠️ My Allergen Preferences",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=20)
        
        tk.Label(
            settings_window,
            text="Select allergens you want to be warned about:",
            font=("Arial", 11),
            bg="white",
            fg="#666"
        ).pack(pady=5)
        
        allergen_list = [
            "dairy", "nuts", "peanuts", "gluten", "soy", 
            "eggs", "fish", "shellfish", "coconut", "sesame"
        ]
        
        allergen_vars = {}
        check_frame = tk.Frame(settings_window, bg="white")
        check_frame.pack(pady=20)
        
        for i, allergen in enumerate(allergen_list):
            var = tk.BooleanVar(value=allergen in self.user_allergens)
            allergen_vars[allergen] = var
            
            cb = tk.Checkbutton(
                check_frame,
                text=allergen.capitalize(),
                variable=var,
                font=("Arial", 12),
                bg="white",
                selectcolor="#4caf50"
            )
            cb.grid(row=i//2, column=i%2, sticky='w', padx=20, pady=5)
        
        def save_settings():
            selected_allergens = {allergen for allergen, var in allergen_vars.items() if var.get()}
            self.save_user_allergens(selected_allergens)
            
            allergen_count = len(selected_allergens)
            allergen_text = f"⚠️ {allergen_count} Allergen(s) Set" if allergen_count > 0 else "No Allergens Set"
            self.allergen_status_label.config(
                text=allergen_text,
                fg="#f44336" if allergen_count > 0 else "#666"
            )
            
            messagebox.showinfo("Success", f"Saved {allergen_count} allergen preference(s)")
            settings_window.destroy()
        
        tk.Button(
            settings_window,
            text="💾 Save Settings",
            command=save_settings,
            bg="#4caf50",
            fg="white",
            font=("Arial", 13, "bold"),
            width=20,
            height=2
        ).pack(pady=20)
        
        tk.Button(
            settings_window,
            text="Cancel",
            command=settings_window.destroy,
            bg="#757575",
            fg="white",
            font=("Arial", 11),
            width=20
        ).pack(pady=5)
        
    def show_welcome_message(self):
        """Show welcome message"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        welcome_text = "👋 Welcome!\n\nScan a barcode to get started\n\n💡 Set your allergens in Settings"
        if SENSEHAT_AVAILABLE:
            welcome_text += "\n\n🕹️ Use joystick to navigate"
            
        welcome = tk.Label(
            self.results_frame,
            text=welcome_text,
            font=("Arial", 13),
            bg="white",
            fg="#666"
        )
        welcome.pack(pady=50)
        
    def refresh_connection(self):
        """Refresh connection status"""
        self.is_online = self.check_connection()
        status_color = "#4caf50" if self.is_online else "#ff9800"
        status_text = "🟢 ONLINE" if self.is_online else "🟠 OFFLINE"
        self.status_label.config(text=status_text, fg=status_color)
        
        mode = "ONLINE" if self.is_online else "OFFLINE"
        messagebox.showinfo("Connection Status", f"Mode: {mode}")
        
    def start_camera_scan(self):
        """Start camera"""
        self.scanning = True
        self.start_camera_btn.config(state=tk.DISABLED)
        self.stop_camera_btn.config(state=tk.NORMAL)
        threading.Thread(target=self.camera_scan_loop, daemon=True).start()
        
    def camera_scan_loop(self):
        """Camera loop - runs in separate thread"""
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        while self.scanning:
            ret, frame = self.camera.read()
            if not ret:
                break
                
            barcodes = pyzbar.decode(frame)
            
            for barcode in barcodes:
                barcode_data = barcode.data.decode('utf-8')
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                cv2.putText(frame, barcode_data, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                self.scanning = False
                self.root.after(0, self.process_barcode, barcode_data)
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            frame_pil = frame_pil.resize((480, 360))
            frame_tk = ImageTk.PhotoImage(frame_pil)
            
            self.camera_label.config(image=frame_tk, text="")
            self.camera_label.image = frame_tk
            
        if self.camera:
            self.camera.release()
            self.camera = None
            
    def stop_camera_scan(self):
        """Stop camera"""
        self.scanning = False
        self.start_camera_btn.config(state=tk.NORMAL)
        self.stop_camera_btn.config(state=tk.DISABLED)
        self.camera_label.config(image='', text="Camera Stopped", bg="black", fg="white")
        
    def upload_image(self):
        """Upload image and scan for barcode - FIXED VERSION"""
        print("📁 Opening file dialog...")
        file_path = filedialog.askopenfilename(
            title="Select Barcode Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            print("❌ No file selected")
            return
            
        print(f"📸 Selected file: {file_path}")
        
        try:
            # Read image with OpenCV
            image = cv2.imread(file_path)
            
            if image is None:
                print("❌ Could not read image file")
                messagebox.showerror("Error", "Could not read image file.\nPlease select a valid image.")
                return
            
            print(f"✅ Image loaded: {image.shape}")
            
            # Display the uploaded image
            display_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            display_pil = Image.fromarray(display_image)
            display_pil = display_pil.resize((480, 360), Image.Resampling.LANCZOS)
            display_tk = ImageTk.PhotoImage(display_pil)
            
            self.camera_label.config(image=display_tk, text="")
            self.camera_label.image = display_tk
            self.root.update()
            
            print("🔍 Decoding barcodes...")
            
            # Decode barcodes
            barcodes = pyzbar.decode(image)
            
            if barcodes:
                barcode_data = barcodes[0].data.decode('utf-8')
                print(f"✅ Barcode found: {barcode_data}")
                self.process_barcode(barcode_data)
            else:
                print("❌ No barcode detected in image")
                messagebox.showerror(
                    "No Barcode Found", 
                    "No barcode detected in the image.\n\n" +
                    "Tips:\n" +
                    "• Ensure the barcode is clear and in focus\n" +
                    "• Try better lighting conditions\n" +
                    "• Use a higher resolution image\n" +
                    "• Make sure the entire barcode is visible"
                )
                
        except Exception as e:
            print(f"❌ Error processing image: {e}")
            messagebox.showerror("Error", f"Failed to process image:\n\n{str(e)}")
            
    def manual_entry(self):
        """Manual entry"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual Barcode Entry")
        dialog.geometry("400x180")
        dialog.configure(bg="white")
        dialog.grab_set()  # Make modal
        
        tk.Label(
            dialog,
            text="Enter Barcode:",
            font=("Arial", 12),
            bg="white"
        ).pack(pady=10)
        
        entry = tk.Entry(dialog, font=("Arial", 14), width=25)
        entry.pack(pady=10)
        entry.focus()
        
        def submit():
            barcode = entry.get().strip()
            if barcode:
                dialog.destroy()
                self.process_barcode(barcode)
            else:
                messagebox.showerror("Error", "Please enter a barcode")
        
        submit_btn = tk.Button(
            dialog,
            text="✓ Submit",
            command=submit,
            bg="#4caf50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2
        )
        submit_btn.pack(pady=10)
        
        entry.bind('<Return>', lambda e: submit())
        
    def process_barcode(self, barcode):
        """Process barcode"""
        print(f"🔄 Processing barcode: {barcode}")
        
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        loading = tk.Label(
            self.results_frame,
            text="⏳ Loading...",
            font=("Arial", 16),
            bg="white"
        )
        loading.pack(pady=50)
        self.root.update()
        
        product = self.get_product_data(barcode)
        
        if product:
            self.display_product_info(product)
        else:
            self.display_error(f"Product not found for barcode: {barcode}")
            self.set_led_color(OFF)
            
    def get_product_data(self, barcode):
        """Get product from API or cache"""
        product = None
        
        if self.is_online:
            try:
                print(f"🌐 API call: {API_BASE_URL}/get_product.php?barcode={barcode}")
                response = requests.get(
                    f"{API_BASE_URL}/get_product.php?barcode={barcode}",
                    timeout=5
                )
                
                print(f"📡 Response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        product = data.get('data')
                        self.cache_product(product)
                        print(f"✅ Fetched from database: {product['name']}")
                    else:
                        print(f"❌ API error: {data.get('error')}")
                else:
                    print(f"❌ HTTP error: {response.status_code}")
            except Exception as e:
                print(f"❌ API Error: {e}")
                
        if not product:
            product = self.get_cached_product(barcode)
            if product:
                print(f"✅ Loaded from cache: {product['name']}")
            
        return product
        
    def cache_product(self, product):
        """Cache product"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        allergens_str = ','.join(product.get('allergens', [])) if isinstance(product.get('allergens'), list) else product.get('allergens', '')
        
        cursor.execute('''
            INSERT OR REPLACE INTO products 
            (barcode, name, brand, category, calories, protein, carbs, sugar, fats, 
             saturated_fats, fiber, sodium, allergens, health_score, is_healthy, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            product['barcode'], product['name'], product.get('brand'), product.get('category'),
            product.get('calories'), product.get('protein'), product.get('carbs'), 
            product.get('sugar'), product.get('fats'), product.get('saturated_fats'),
            product.get('fiber'), product.get('sodium'), allergens_str,
            product.get('health_score'), product.get('is_healthy')
        ))
        
        cursor.execute('INSERT INTO scan_history (barcode) VALUES (?)', (product['barcode'],))
        conn.commit()
        conn.close()
        
    def get_cached_product(self, barcode):
        """Get from cache"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM products WHERE barcode = ?', (barcode,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'barcode', 'name', 'brand', 'category', 'calories', 'protein', 'carbs', 
                      'sugar', 'fats', 'saturated_fats', 'fiber', 'sodium', 'allergens', 
                      'health_score', 'is_healthy', 'cached_at']
            product = dict(zip(columns, row))
            if product['allergens']:
                product['allergens'] = product['allergens'].split(',')
            else:
                product['allergens'] = []
            return product
        return None
        
    def display_product_info(self, product):
        """Display product"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        # Check allergens
        product_allergens = set(product.get('allergens', []))
        if isinstance(product.get('allergens'), str):
            product_allergens = set(product['allergens'].split(',')) if product['allergens'] else set()
        
        has_allergen = bool(self.user_allergens & product_allergens)
        
        # Set LED based on allergen and health
        if has_allergen:
            self.set_led_color(RED, 'flash')
        elif product.get('is_healthy'):
            self.set_led_color(GREEN, 'solid')
        else:
            self.set_led_color(ORANGE, 'solid')
            
        # Product name
        name_label = tk.Label(
            self.results_frame,
            text=product['name'],
            font=("Arial", 18, "bold"),
            bg="white",
            wraplength=350
        )
        name_label.pack(pady=10)
        
        if product.get('brand'):
            brand_label = tk.Label(
                self.results_frame,
                text=product['brand'],
                font=("Arial", 12),
                bg="white",
                fg="#666"
            )
            brand_label.pack()
            
        # Allergen warning
        if has_allergen:
            allergen_frame = tk.LabelFrame(
                self.results_frame,
                text="🚨 ALLERGEN ALERT",
                font=("Arial", 14, "bold"),
                bg="#ffebee",
                fg="#f44336",
                relief=tk.RAISED,
                bd=3
            )
            allergen_frame.pack(pady=15, padx=20, fill=tk.X)
            
            matching_allergens = self.user_allergens & product_allergens
            allergens_text = ", ".join([a.upper() for a in matching_allergens])
            
            tk.Label(
                allergen_frame,
                text=f"⚠️ Contains: {allergens_text}",
                font=("Arial", 12, "bold"),
                bg="#ffebee",
                fg="#f44336",
                wraplength=350
            ).pack(padx=10, pady=10)
            
        # Health score
        health_score = product.get('health_score', 50)
        score_color = "#4caf50" if health_score >= 70 else "#ff9800" if health_score >= 40 else "#f44336"
        
        score_frame = tk.Frame(self.results_frame, bg=score_color, relief=tk.RAISED, bd=2)
        score_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(
            score_frame,
            text=f"Health Score: {health_score}/100",
            font=("Arial", 14, "bold"),
            bg=score_color,
            fg="white"
        ).pack(pady=10)
        
        # Nutrition
        nutrition_frame = tk.LabelFrame(
            self.results_frame,
            text="Nutrition Facts (per 100g)",
            font=("Arial", 12, "bold"),
            bg="white"
        )
        nutrition_frame.pack(pady=10, padx=20, fill=tk.X)
        
        nutrition_data = [
            ("Calories", product.get('calories'), "kcal"),
            ("Protein", product.get('protein'), "g"),
            ("Carbs", product.get('carbs'), "g"),
            ("Sugar", product.get('sugar'), "g"),
            ("Fats", product.get('fats'), "g"),
            ("Fiber", product.get('fiber'), "g"),
            ("Sodium", product.get('sodium'), "g"),
        ]
        
        for label, value, unit in nutrition_data:
            if value is not None:
                row = tk.Frame(nutrition_frame, bg="white")
                row.pack(fill=tk.X, padx=10, pady=2)
                
                tk.Label(
                    row,
                    text=label,
                    font=("Arial", 11),
                    bg="white",
                    anchor="w"
                ).pack(side=tk.LEFT)
                
                tk.Label(
                    row,
                    text=f"{value} {unit}",
                    font=("Arial", 11, "bold"),
                    bg="white",
                    anchor="e"
                ).pack(side=tk.RIGHT)
                
        # All allergens
        if product_allergens and len(product_allergens) > 0:
            allergen_frame2 = tk.LabelFrame(
                self.results_frame,
                text="Contains Allergens",
                font=("Arial", 11, "bold"),
                bg="white"
            )
            allergen_frame2.pack(pady=10, padx=20, fill=tk.X)
            
            allergens_text = ", ".join([a.capitalize() for a in product_allergens])
            tk.Label(
                allergen_frame2,
                text=allergens_text,
                font=("Arial", 10),
                bg="white",
                fg="#666",
                wraplength=350
            ).pack(padx=10, pady=5)
            
    def display_error(self, message):
        """Display error"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
            
        error_label = tk.Label(
            self.results_frame,
            text="❌ Error",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#f44336"
        )
        error_label.pack(pady=20)
        
        message_label = tk.Label(
            self.results_frame,
            text=message,
            font=("Arial", 12),
            bg="white",
            wraplength=350
        )
        message_label.pack(pady=10)

def main():
    root = tk.Tk()
    app = NutritionScannerApp(root)
    
    try:
        root.mainloop()
    finally:
        if SENSEHAT_AVAILABLE:
            sense.clear()
        print("👋 Application closed")

if __name__ == "__main__":
    main()