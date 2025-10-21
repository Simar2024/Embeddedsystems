"""
Smart Barcode Nutrition Scanner
Main Application - Raspberry Pi with SenseHat + Joystick
Python 3.7+

Run: python3 main.py
Exit Fullscreen: Press ESC or F11
Control: Use MOUSE or JOYSTICK (UP/DOWN to navigate, MIDDLE to select)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
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
import time

# Try to import SenseHat (only works on Raspberry Pi)
try:
    from sense_hat import SenseHat
    SENSEHAT_AVAILABLE = True
    sense = SenseHat()
    sense.clear()
except ImportError:
    SENSEHAT_AVAILABLE = False
    print("WARNING: SenseHat not available - LED features disabled (running on non-RPi?)")

# Configuration
API_BASE_URL = "http://localhost/api"  # Change if API is hosted elsewhere
SQLITE_DB = "nutrition_cache.db"
PICTURES_DIR = "/home/pi/Pictures"  # Changed to specific path

# Create Pictures directory if it doesn't exist
if not os.path.exists(PICTURES_DIR):
    try:
        os.makedirs(PICTURES_DIR)
        print(f"Created directory: {PICTURES_DIR}")
    except:
        # Fallback to current directory if /home/pi/Pictures doesn't work
        PICTURES_DIR = os.path.join(os.getcwd(), "Pictures")
        if not os.path.exists(PICTURES_DIR):
            os.makedirs(PICTURES_DIR)
        print(f"Using fallback directory: {PICTURES_DIR}")

# LED Colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
ORANGE = (255, 165, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
OFF = (0, 0, 0)

# Arrow patterns for SenseHat
ARROW_UP = [
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF,
    OFF, OFF, WHITE, WHITE, WHITE, WHITE, OFF, OFF,
    OFF, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, OFF,
    WHITE, WHITE, OFF, WHITE, WHITE, OFF, WHITE, WHITE,
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF,
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF,
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF,
    OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF
]

ARROW_DOWN = [
    OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF,
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF,
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF,
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF,
    WHITE, WHITE, OFF, WHITE, WHITE, OFF, WHITE, WHITE,
    OFF, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, OFF,
    OFF, OFF, WHITE, WHITE, WHITE, WHITE, OFF, OFF,
    OFF, OFF, OFF, WHITE, WHITE, OFF, OFF, OFF
]

ARROW_LEFT = [
    OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF,
    OFF, OFF, WHITE, OFF, OFF, OFF, OFF, OFF,
    OFF, WHITE, WHITE, OFF, OFF, OFF, OFF, OFF,
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, OFF,
    WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, OFF,
    OFF, WHITE, WHITE, OFF, OFF, OFF, OFF, OFF,
    OFF, OFF, WHITE, OFF, OFF, OFF, OFF, OFF,
    OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF
]

ARROW_RIGHT = [
    OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF,
    OFF, OFF, OFF, OFF, OFF, WHITE, OFF, OFF,
    OFF, OFF, OFF, OFF, OFF, WHITE, WHITE, OFF,
    OFF, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,
    OFF, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE, WHITE,
    OFF, OFF, OFF, OFF, OFF, WHITE, WHITE, OFF,
    OFF, OFF, OFF, OFF, OFF, WHITE, OFF, OFF,
    OFF, OFF, OFF, OFF, OFF, OFF, OFF, OFF
]


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
        self.led_animation_running = False
        
        # Variables for Add Product feature
        self.adding_product = False
        self.captured_image = None
        self.captured_barcode = None
        self.capture_ready = False
        self.detected_barcode = None
        self.latest_frame = None
        
        # Joystick variables
        self.joystick_thread = None
        self.joystick_running = False
        self.joystick_enabled = True
        self.current_menu_index = 0
        self.menu_items = []
        
        # Statistics
        self.total_scans = self.get_total_scans()
        self.healthy_scans = self.get_healthy_scans()
        self.allergen_warnings = self.get_allergen_warnings()
        
        # Create GUI
        self.create_gui()
        
        # Start joystick listener if enabled
        if SENSEHAT_AVAILABLE and self.joystick_enabled:
            self.start_joystick_listener()
            self.show_arrow_pattern(ARROW_UP)
        
        print("SUCCESS: Application started successfully")
        print("INFO: Mouse control is always enabled")
        if SENSEHAT_AVAILABLE:
            print("SUCCESS: SenseHat LED matrix ready")
            if self.joystick_enabled:
                print("SUCCESS: Joystick navigation enabled - UP/DOWN to navigate, MIDDLE to select")
    
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
                scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_healthy INTEGER,
                has_allergen INTEGER
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
        print("SUCCESS: SQLite database initialized")
    
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
    
    def get_total_scans(self):
        """Get total number of scans"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scan_history")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_healthy_scans(self):
        """Get number of healthy product scans"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scan_history WHERE is_healthy = 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_allergen_warnings(self):
        """Get number of allergen warnings"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM scan_history WHERE has_allergen = 1")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def check_connection(self):
        """Check if we have internet connection to API"""
        try:
            response = requests.get(f"{API_BASE_URL}/test_connection.php", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def toggle_joystick(self):
        """Toggle joystick on/off"""
        if not SENSEHAT_AVAILABLE:
            messagebox.showinfo("Joystick", "SenseHat not available - joystick cannot be used")
            return
        
        self.joystick_enabled = not self.joystick_enabled
        
        if self.joystick_enabled:
            self.start_joystick_listener()
            self.joystick_toggle_btn.config(text="Joystick: ON", bg="#4caf50")
            messagebox.showinfo("Joystick", "Joystick control ENABLED")
            self.show_arrow_pattern(ARROW_UP)
        else:
            self.joystick_running = False
            self.joystick_toggle_btn.config(text="Joystick: OFF", bg="#757575")
            messagebox.showinfo("Joystick", "Joystick control DISABLED\nMouse control still active")
            if SENSEHAT_AVAILABLE:
                sense.clear()
    
    def show_arrow_pattern(self, pattern):
        """Show arrow pattern on SenseHat"""
        if not SENSEHAT_AVAILABLE or not self.joystick_enabled:
            return
        sense.set_pixels(pattern)
    
    def set_led_color(self, color, pattern='solid'):
        """Set SenseHat LED color"""
        if not SENSEHAT_AVAILABLE:
            return
        
        self.led_animation_running = False
        if self.led_thread and self.led_thread.is_alive():
            time.sleep(0.1)
        
        if pattern == 'solid':
            sense.clear(color)
        elif pattern == 'flash':
            self.led_animation_running = True
            self.led_thread = threading.Thread(target=self._flash_led, args=(color,), daemon=True)
            self.led_thread.start()
        elif pattern == 'pulse':
            self.led_animation_running = True
            self.led_thread = threading.Thread(target=self._pulse_led, args=(color,), daemon=True)
            self.led_thread.start()
        elif pattern == 'rainbow':
            self.led_animation_running = True
            self.led_thread = threading.Thread(target=self._rainbow_animation, daemon=True)
            self.led_thread.start()
    
    def _flash_led(self, color):
        """Flash LED pattern"""
        for _ in range(6):
            if not self.led_animation_running:
                break
            sense.clear(color)
            time.sleep(0.3)
            sense.clear()
            time.sleep(0.3)
        if self.led_animation_running:
            sense.clear(color)
    
    def _pulse_led(self, color):
        """Pulse LED pattern"""
        r, g, b = color
        for _ in range(3):
            if not self.led_animation_running:
                break
            for brightness in range(0, 100, 5):
                if not self.led_animation_running:
                    break
                dim_color = (r * brightness // 100, g * brightness // 100, b * brightness // 100)
                sense.clear(dim_color)
                time.sleep(0.02)
            for brightness in range(100, 0, -5):
                if not self.led_animation_running:
                    break
                dim_color = (r * brightness // 100, g * brightness // 100, b * brightness // 100)
                sense.clear(dim_color)
                time.sleep(0.02)
        if self.led_animation_running:
            sense.clear(color)
    
    def _rainbow_animation(self):
        """Rainbow animation for SenseHat"""
        colors = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE]
        for _ in range(10):
            if not self.led_animation_running:
                break
            for color in colors:
                if not self.led_animation_running:
                    break
                sense.clear(color)
                time.sleep(0.1)
    
    def _update_camera_label_from_array(self, frame):
        """Update camera label with frame"""
        try:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_pil = Image.fromarray(frame_rgb)
            frame_pil = frame_pil.resize((480, 360))
            frame_tk = ImageTk.PhotoImage(frame_pil)
            self.camera_label.config(image=frame_tk, text="")
            self.camera_label.image = frame_tk
        except:
            pass
    
    def _set_capture_status_safe(self, text, color):
        """Safely set capture status text"""
        self.capture_status_label.config(text=text, fg=color)
    
    def _enable_capture_button(self, enabled):
        """Enable or disable capture button"""
        if enabled:
            self.capture_btn.config(state=tk.NORMAL, bg="#4caf50")
        else:
            self.capture_btn.config(state=tk.DISABLED, bg="#757575")
    
    def start_joystick_listener(self):
        """Start listening to joystick events"""
        if not SENSEHAT_AVAILABLE or not self.joystick_enabled:
            return
        
        self.joystick_running = True
        self.joystick_thread = threading.Thread(target=self._joystick_loop, daemon=True)
        self.joystick_thread.start()
    
    def _joystick_loop(self):
        """Joystick event loop - runs in separate thread"""
        while self.joystick_running and self.joystick_enabled:
            try:
                for event in sense.stick.get_events():
                    if event.action == "pressed":
                        if event.direction == "up":
                            self.root.after(0, self.joystick_up)
                        elif event.direction == "down":
                            self.root.after(0, self.joystick_down)
                        elif event.direction == "left":
                            self.root.after(0, self.joystick_left)
                        elif event.direction == "right":
                            self.root.after(0, self.joystick_right)
                        elif event.direction == "middle":
                            self.root.after(0, self.joystick_select)
            except:
                pass
            time.sleep(0.05)
    
    def joystick_up(self):
        """Handle joystick UP - navigate menu"""
        if len(self.menu_items) > 0:
            self.current_menu_index = (self.current_menu_index - 1) % len(self.menu_items)
            self.highlight_menu_item()
            self.show_arrow_pattern(ARROW_UP)
    
    def joystick_down(self):
        """Handle joystick DOWN - navigate menu"""
        if len(self.menu_items) > 0:
            self.current_menu_index = (self.current_menu_index + 1) % len(self.menu_items)
            self.highlight_menu_item()
            self.show_arrow_pattern(ARROW_DOWN)
    
    def joystick_left(self):
        """Handle joystick LEFT"""
        self.show_arrow_pattern(ARROW_LEFT)
        self.refresh_connection()
    
    def joystick_right(self):
        """Handle joystick RIGHT"""
        self.show_arrow_pattern(ARROW_RIGHT)
        self.open_settings()
    
    def joystick_select(self):
        """Handle joystick MIDDLE - select current menu item"""
        if len(self.menu_items) > 0:
            selected_button = self.menu_items[self.current_menu_index]
            selected_button.invoke()
            self.set_led_color(GREEN, 'pulse')
    
    def highlight_menu_item(self):
        """Highlight current menu item"""
        for i, btn in enumerate(self.menu_items):
            if i == self.current_menu_index:
                btn.configure(relief=tk.RAISED, borderwidth=4, bg="#2196f3")
            else:
                original_bg = self.menu_original_bg[i] if hasattr(self, 'menu_original_bg') and i < len(self.menu_original_bg) else btn.cget("bg")
                btn.configure(relief=tk.FLAT, borderwidth=1, bg=original_bg)
    
    def quit_app(self):
        """Quit application and cleanup"""
        self.joystick_running = False
        self.led_animation_running = False
        if SENSEHAT_AVAILABLE:
            sense.clear()
        if self.camera:
            self.camera.release()
        self.root.quit()
    
    def create_gui(self):
        """Create the main GUI interface"""
        # Title bar
        title_frame = tk.Frame(self.root, bg="#4a90e2", height=70)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="Smart Nutrition Scanner",
            font=("Arial", 20, "bold"),
            bg="#4a90e2",
            fg="white"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        control_label = tk.Label(
            title_frame,
            text="Control: Mouse (Always) | Joystick (Toggle)",
            font=("Arial", 10),
            bg="#4a90e2",
            fg="white"
        )
        control_label.pack(side=tk.LEFT, padx=10, pady=15)
        
        if SENSEHAT_AVAILABLE:
            self.joystick_toggle_btn = tk.Button(
                title_frame,
                text="Joystick: ON" if self.joystick_enabled else "Joystick: OFF",
                command=self.toggle_joystick,
                bg="#4caf50" if self.joystick_enabled else "#757575",
                fg="white",
                font=("Arial", 11, "bold"),
                relief=tk.FLAT,
                padx=15,
                pady=8
            )
            self.joystick_toggle_btn.pack(side=tk.LEFT, padx=10, pady=15)
        
        exit_btn = tk.Button(
            title_frame,
            text="EXIT",
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
        status_text = "ONLINE" if self.is_online else "OFFLINE"
        
        self.status_label = tk.Label(
            status_frame,
            text=status_text,
            font=("Arial", 12, "bold"),
            bg="#e8e8e8",
            fg=status_color
        )
        self.status_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        allergen_count = len(self.user_allergens)
        allergen_text = f"Allergens: {allergen_count} Set" if allergen_count > 0 else "No Allergens Set"
        self.allergen_status_label = tk.Label(
            status_frame,
            text=allergen_text,
            font=("Arial", 11),
            bg="#e8e8e8",
            fg="#f44336" if allergen_count > 0 else "#666"
        )
        self.allergen_status_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.scan_counter_label = tk.Label(
            status_frame,
            text=f"Total Scans: {self.total_scans}",
            font=("Arial", 11),
            bg="#e8e8e8",
            fg="#2196f3"
        )
        self.scan_counter_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        if SENSEHAT_AVAILABLE:
            led_status = tk.Label(
                status_frame,
                text="LED Ready | Joystick Active" if self.joystick_enabled else "LED Ready",
                font=("Arial", 11),
                bg="#e8e8e8",
                fg="#4caf50"
            )
            led_status.pack(side=tk.LEFT, padx=20, pady=10)
        
        settings_btn = tk.Button(
            status_frame,
            text="Settings",
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
            text="Refresh",
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
            text="Scan Area",
            font=("Arial", 14, "bold"),
            bg="white"
        )
        scan_title.pack(pady=10)
        
        self.camera_label = tk.Label(left_frame, bg="black", text="Camera Off", fg="white", font=("Arial", 16))
        self.camera_label.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Status label for capture instructions
        self.capture_status_label = tk.Label(left_frame, text="", font=("Arial", 12), bg="white", fg="#2196f3")
        self.capture_status_label.pack()
        
        # Capture button (initially hidden)
        self.capture_btn = tk.Button(
            left_frame,
            text="CAPTURE IMAGE",
            command=self.capture_product_image,
            bg="#4caf50",
            fg="white",
            font=("Arial", 14, "bold"),
            width=20,
            height=2,
            cursor="hand2"
        )
        # Don't pack it yet - will be shown only during add product mode
        
        # Buttons
        btn_frame = tk.Frame(left_frame, bg="white")
        btn_frame.pack(pady=15)
        
        upload_btn = tk.Button(
            btn_frame,
            text="Upload\nImage",
            command=self.upload_image,
            bg="#2196f3",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3,
            cursor="hand2"
        )
        upload_btn.grid(row=0, column=0, padx=5)
        self.menu_items.append(upload_btn)
        
        manual_btn = tk.Button(
            btn_frame,
            text="Manual\nEntry",
            command=self.manual_entry,
            bg="#ff9800",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3,
            cursor="hand2"
        )
        manual_btn.grid(row=0, column=1, padx=5)
        self.menu_items.append(manual_btn)
        
        history_btn = tk.Button(
            btn_frame,
            text="View\nHistory",
            command=self.view_history,
            bg="#9c27b0",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3,
            cursor="hand2"
        )
        history_btn.grid(row=1, column=0, padx=5, pady=5)
        self.menu_items.append(history_btn)
        
        stats_btn = tk.Button(
            btn_frame,
            text="View\nStatistics",
            command=self.view_statistics,
            bg="#00bcd4",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3,
            cursor="hand2"
        )
        stats_btn.grid(row=1, column=1, padx=5, pady=5)
        self.menu_items.append(stats_btn)
        
        # Add Product buttons (Barcode/Image)
        add_product_barcode_btn = tk.Button(
            btn_frame,
            text="Add Product\n(Barcode)",
            command=self.start_add_product_with_barcode,
            bg="#ff5722",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3,
            cursor="hand2"
        )
        add_product_barcode_btn.grid(row=2, column=0, padx=5, pady=5)
        self.menu_items.append(add_product_barcode_btn)

        add_product_image_btn = tk.Button(
            btn_frame,
            text="Add Product\n(Image)",
            command=self.start_add_product_with_image,
            bg="#ff7043",
            fg="white",
            font=("Arial", 13, "bold"),
            width=12,
            height=3,
            cursor="hand2"
        )
        add_product_image_btn.grid(row=2, column=1, padx=5, pady=5)
        self.menu_items.append(add_product_image_btn)
        
        # Right panel - Results
        right_frame = tk.Frame(main_frame, bg="white", relief=tk.RAISED, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        results_title = tk.Label(
            right_frame,
            text="Nutrition Information",
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
        self.current_menu_index = 0
        self.menu_original_bg = [btn.cget("bg") for btn in self.menu_items]
        if self.menu_items:
            self.highlight_menu_item()
    
    def show_welcome_message(self):
        """Show welcome message"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        welcome_text = "Welcome!\n\nScan a barcode to get started\n\nSet your allergens in Settings"
        welcome_text += "\n\nMouse control is always enabled"
        if SENSEHAT_AVAILABLE:
            welcome_text += "\nToggle joystick control in title bar"
        
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
        status_text = "ONLINE" if self.is_online else "OFFLINE"
        self.status_label.config(text=status_text, fg=status_color)
        
        if SENSEHAT_AVAILABLE:
            if self.is_online:
                self.set_led_color(GREEN, 'pulse')
            else:
                self.set_led_color(ORANGE, 'pulse')
        
        mode = "ONLINE" if self.is_online else "OFFLINE"
        messagebox.showinfo("Connection Status", f"Mode: {mode}")
    
    def open_settings(self):
        """Open allergen settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x650")
        settings_window.configure(bg="white")
        settings_window.grab_set()
        
        tk.Label(
            settings_window,
            text="My Allergen Preferences",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=20)
        
        tk.Label(
            settings_window,
            text="Select your allergens:",
            font=("Arial", 12),
            bg="white",
            fg="#666"
        ).pack(pady=10)
        
        # Allergen checkboxes
        allergen_list = ["dairy", "nuts", "peanuts", "gluten", "soy", 
                        "eggs", "fish", "shellfish", "coconut", "sesame"]
        allergen_vars = {}
        
        allergen_frame = tk.Frame(settings_window, bg="white")
        allergen_frame.pack(pady=20)
        
        for allergen in allergen_list:
            var = tk.BooleanVar()
            var.set(allergen in self.user_allergens)
            allergen_vars[allergen] = var
            
            cb = tk.Checkbutton(
                allergen_frame,
                text=allergen.capitalize(),
                variable=var,
                font=("Arial", 12),
                bg="white",
                anchor="w"
            )
            cb.pack(fill=tk.X, padx=20, pady=5)
        
        def save_allergens():
            selected_allergens = set()
            for allergen, var in allergen_vars.items():
                if var.get():
                    selected_allergens.add(allergen)
            
            self.save_user_allergens(selected_allergens)
            
            allergen_count = len(self.user_allergens)
            allergen_text = f"Allergens: {allergen_count} Set" if allergen_count > 0 else "No Allergens Set"
            self.allergen_status_label.config(
                text=allergen_text,
                fg="#f44336" if allergen_count > 0 else "#666"
            )
            
            messagebox.showinfo("Success", f"Allergen preferences saved!\n\n{allergen_count} allergen(s) set.")
            settings_window.destroy()
        
        # Buttons
        btn_frame = tk.Frame(settings_window, bg="white")
        btn_frame.pack(pady=30)
        
        save_btn = tk.Button(
            btn_frame,
            text="Save",
            command=save_allergens,
            bg="#4caf50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
            cursor="hand2"
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=settings_window.destroy,
            bg="#757575",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
            cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def start_add_product_with_barcode(self):
        """Add product by entering a barcode (no camera)"""
        if not self.is_online:
            messagebox.showerror(
                "Offline Mode",
                "You must be ONLINE to add new products to the database.\n\nPlease connect to the internet and try again."
            )
            return
        
        barcode = simpledialog.askstring("Add Product (Barcode)", "Enter Barcode:")
        if not barcode:
            return
        
        # Remove leading zero for UPC-A conversion if needed
        if len(barcode) == 13 and barcode.startswith('0'):
            barcode = barcode[1:]
        
        self.open_add_product_form(barcode, None)

    def start_add_product_with_image(self):
        """Add product using camera (manual/auto capture), then fill details"""
        self.start_add_product()
    
    def start_add_product(self):
        """Start the process of adding a new product"""
        if not self.is_online:
            messagebox.showerror(
                "Offline Mode",
                "You must be ONLINE to add new products to the database.\n\n" +
                "Please connect to the internet and try again."
            )
            return
        
        # Ask user for capture mode
        mode_dialog = tk.Toplevel(self.root)
        mode_dialog.title("Choose Capture Mode")
        mode_dialog.geometry("420x250")
        mode_dialog.configure(bg="white")
        mode_dialog.transient(self.root)
        mode_dialog.lift()
        mode_dialog.grab_set()
        mode_dialog.focus_force()
        
        tk.Label(
            mode_dialog,
            text="Select Capture Mode",
            font=("Arial", 14, "bold"),
            bg="white"
        ).pack(pady=20)
        
        mode_var = tk.StringVar(master=mode_dialog, value="manual")
        
        tk.Radiobutton(
            mode_dialog,
            text="Manual Capture (Click button when ready)",
            variable=mode_var,
            value="manual",
            font=("Arial", 12),
            bg="white"
        ).pack(pady=5)
        
        tk.Radiobutton(
            mode_dialog,
            text="Auto Capture (Captures immediately on detection)",
            variable=mode_var,
            value="auto",
            font=("Arial", 12),
            bg="white"
        ).pack(pady=5)
        
        def start_capture():
            capture_mode = mode_var.get()
            print(f"INFO: Selected capture mode: {capture_mode}")
            mode_dialog.destroy()
            
            self.adding_product = True
            self.captured_image = None
            self.captured_barcode = None
            self.capture_ready = False
            self.detected_barcode = None
            self.scanning = True
            
            if capture_mode == "manual":
                self.capture_btn.pack(pady=10)
                self.capture_btn.config(state=tk.DISABLED, bg="#757575")
                
                messagebox.showinfo(
                    "Manual Capture Mode",
                    "1. Point camera at barcode\n" +
                    "2. Button turns green when barcode detected\n" +
                    "3. Click CAPTURE IMAGE button\n\n" +
                    f"Saves to: {PICTURES_DIR}"
                )
                threading.Thread(target=lambda: self.add_product_camera_loop(auto_capture=False), daemon=True).start()
            else:
                messagebox.showinfo(
                    "Auto Capture Mode",
                    "Point camera at barcode.\n" +
                    "Image captures automatically on detection.\n\n" +
                    f"Saves to: {PICTURES_DIR}"
                )
                threading.Thread(target=lambda: self.add_product_camera_loop(auto_capture=True), daemon=True).start()
        
        tk.Button(
            mode_dialog,
            text="Start",
            command=start_capture,
            bg="#4caf50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2
        ).pack(pady=20)
    
    def add_product_camera_loop(self, auto_capture=False):
        """Camera loop for adding products - supports both auto and manual capture"""
        # Try to open camera with multiple methods
        chosen_idx = None
        backends = [None]
        if hasattr(cv2, 'CAP_DSHOW'):
            backends.append(cv2.CAP_DSHOW)
        if hasattr(cv2, 'CAP_MSMF'):
            backends.append(cv2.CAP_MSMF)
        
        for idx in [0, 1, 2, 3]:
            for backend in backends:
                try:
                    if backend is None:
                        print(f"INFO: Trying camera index {idx} with default backend...")
                        cam = cv2.VideoCapture(idx)
                    else:
                        print(f"INFO: Trying camera index {idx} with backend {backend}...")
                        cam = cv2.VideoCapture(idx, backend)
                except Exception as e:
                    print(f"WARN: VideoCapture failed: idx={idx}, backend={backend}, err={e}")
                    cam = None
                    
                if cam is not None and cam.isOpened():
                    self.camera = cam
                    chosen_idx = idx
                    break
            if chosen_idx is not None:
                break
        
        if not hasattr(self, 'camera') or self.camera is None or not self.camera.isOpened():
            print("ERROR: No camera device opened")
            self.root.after(0, lambda: messagebox.showerror(
                "Camera Error", 
                "Could not open camera. Please ensure a camera is connected and not in use."
            ))
            self.scanning = False
            self.adding_product = False
            return
        
        print(f"SUCCESS: Opened camera at index {chosen_idx}")
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        captured = False
        no_barcode_count = 0
        
        while self.scanning and self.adding_product and not captured:
            ret, frame = self.camera.read()
            if not ret:
                break
            
            # Keep a copy of the original frame for saving
            original_frame = frame.copy()
            self.latest_frame = original_frame
            
            barcodes = pyzbar.decode(frame)
            
            if barcodes:
                barcode = barcodes[0]
                barcode_data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                
                print(f"INFO: Detected barcode: {barcode_data} (Type: {barcode_type})")
                
                # Remove leading zero for UPC-A conversion if needed
                if len(barcode_data) == 13 and barcode_data.isdigit() and barcode_data.startswith('0'):
                    barcode_data = barcode_data[1:]
                    print(f"INFO: Converted to UPC-A: {barcode_data}")
                
                # Store detected barcode and frame
                self.detected_barcode = barcode_data
                self.captured_image = original_frame
                self.capture_ready = True
                
                # Draw rectangle around barcode
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                cv2.putText(frame, f"{barcode_data} ({barcode_type})", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if auto_capture:
                    # Auto capture immediately
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    image_filename = f"{barcode_data}_{timestamp}.jpg"
                    image_path = os.path.join(PICTURES_DIR, image_filename)
                    
                    cv2.imwrite(image_path, original_frame)
                    print(f"INFO: Auto-captured and saved to {image_path}")
                    
                    captured = True
                    self.scanning = False
                    self.adding_product = False
                    
                    # Open the add product form
                    self.root.after(0, self.open_add_product_form, barcode_data, image_path)
                else:
                    # Manual mode - enable capture button
                    self.root.after(0, self._set_capture_status_safe, 
                                   f"Barcode detected: {barcode_data}", "green")
                    self.root.after(0, self._enable_capture_button, True)
                
                no_barcode_count = 0
            else:
                self.capture_ready = False
                self.detected_barcode = None
                self.captured_image = None
                no_barcode_count += 1
                
                if no_barcode_count % 30 == 0:
                    self.root.after(0, self._set_capture_status_safe, 
                                   "No barcode found - adjust camera position", "#ff9800")
                if not auto_capture:
                    self.root.after(0, self._enable_capture_button, False)
            
            self.root.after(0, self._update_camera_label_from_array, frame.copy())
        
        if self.camera:
            self.camera.release()
            self.camera = None
            self.root.after(0, lambda: self.capture_status_label.config(text=""))
        self.root.after(0, self.capture_btn.pack_forget)
    
    def capture_product_image(self, event=None):
        """Capture and save product image when button is clicked"""
        if not (self.capture_ready and self.detected_barcode):
            messagebox.showinfo("Unable to Read Barcode", 
                               "No valid barcode detected. Please adjust and try again.")
            return

        # Get frame to save
        frame_to_save = None
        barcode = self.detected_barcode
        
        if getattr(self, 'camera', None) is not None:
            ret, frame = self.camera.read()
            if ret:
                frame_to_save = frame.copy()
        
        if frame_to_save is None and self.captured_image is not None:
            frame_to_save = self.captured_image
            
        if frame_to_save is None:
            messagebox.showerror("Capture Error", "No camera frame available yet. Please try again.")
            return

        # Create filename and save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_base = f"{barcode}_{timestamp}"
        safe_base = ''.join(c if (c.isalnum() or c in ('_', '-', ' ')) else '_' 
                           for c in default_base).strip().replace(' ', '_')
        image_filename = f"{safe_base}.jpg"
        image_path = os.path.join(PICTURES_DIR, image_filename)
        
        # Handle duplicates
        counter = 1
        while os.path.exists(image_path):
            image_filename = f"{safe_base}_{counter}.jpg"
            image_path = os.path.join(PICTURES_DIR, image_filename)
            counter += 1
            
        cv2.imwrite(image_path, frame_to_save)
        print(f"INFO: Saved image to {image_path}")

        # Optional rename
        new_base = simpledialog.askstring("Save Image", 
                                         "Enter file name (without extension):", 
                                         initialvalue=safe_base)
        if new_base and new_base.strip() != safe_base:
            new_base = new_base.strip()
            new_safe = ''.join(c if (c.isalnum() or c in ('_', '-', ' ')) else '_' 
                             for c in new_base).strip().replace(' ', '_')
            new_filename = f"{new_safe}.jpg"
            new_path = os.path.join(PICTURES_DIR, new_filename)
            
            c = 1
            while os.path.exists(new_path):
                new_filename = f"{new_safe}_{c}.jpg"
                new_path = os.path.join(PICTURES_DIR, new_filename)
                c += 1
                
            try:
                os.replace(image_path, new_path)
                image_path = new_path
                print(f"INFO: Renamed image to {image_path}")
            except Exception as e:
                print(f"WARN: Could not rename image: {e}")

        # Stop scanning and hide capture button
        self.scanning = False
        self.adding_product = False
        self.capture_status_label.config(text="Image captured successfully!", fg="#4caf50")
        self.capture_btn.pack_forget()

        # Open the add product form
        self.root.after(0, self.open_add_product_form, barcode, image_path)
    
    def open_add_product_form(self, barcode, image_path):
        """Open form to add product details"""
        self.camera_label.config(image='', text="Product Captured!", bg="green", fg="white")
        
        form_window = tk.Toplevel(self.root)
        form_window.title("Add New Product")
        form_window.geometry("600x800")
        form_window.configure(bg="white")
        form_window.grab_set()
        
        # Scrollable form
        canvas = tk.Canvas(form_window, bg="white")
        scrollbar = ttk.Scrollbar(form_window, orient="vertical", command=canvas.yview)
        form_frame = tk.Frame(canvas, bg="white")
        
        form_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        tk.Label(
            form_frame,
            text="Add New Product to Database",
            font=("Arial", 18, "bold"),
            bg="white"
        ).pack(pady=10)
        
        tk.Label(
            form_frame,
            text=f"Barcode: {barcode}",
            font=("Arial", 12),
            bg="white",
            fg="#666"
        ).pack(pady=5)
        
        if image_path:
            tk.Label(
                form_frame,
                text=f"Image: {os.path.basename(image_path)}",
                font=("Arial", 10),
                bg="white",
                fg="#666"
            ).pack(pady=5)
        
        # Form fields
        fields = {}
        
        def create_field(label_text, field_name, default="", field_type="text"):
            field_frame = tk.Frame(form_frame, bg="white")
            field_frame.pack(fill=tk.X, pady=5, padx=20)
            
            tk.Label(
                field_frame,
                text=label_text,
                font=("Arial", 11, "bold"),
                bg="white",
                anchor="w",
                width=20
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            entry = tk.Entry(field_frame, font=("Arial", 11), width=30)
            entry.insert(0, default)
            entry.pack(side=tk.RIGHT)
            fields[field_name] = entry
        
        # Basic Info
        tk.Label(form_frame, text="Basic Information", 
                font=("Arial", 14, "bold"), bg="white").pack(pady=(20, 10))
        create_field("Product Name *", "name")
        create_field("Brand", "brand")
        create_field("Category", "category")
        
        # Nutrition Info
        tk.Label(form_frame, text="Nutrition (per 100g)", 
                font=("Arial", 14, "bold"), bg="white").pack(pady=(20, 10))
        create_field("Calories (kcal)", "calories", "0", "number")
        create_field("Protein (g)", "protein", "0.0", "number")
        create_field("Carbs (g)", "carbs", "0.0", "number")
        create_field("Sugar (g)", "sugar", "0.0", "number")
        create_field("Fats (g)", "fats", "0.0", "number")
        create_field("Saturated Fats (g)", "saturated_fats", "0.0", "number")
        create_field("Fiber (g)", "fiber", "0.0", "number")
        create_field("Sodium (g)", "sodium", "0.0", "number")
        
        # Allergens
        tk.Label(form_frame, text="Allergens", 
                font=("Arial", 14, "bold"), bg="white").pack(pady=(20, 10))
        
        allergen_list = ["dairy", "nuts", "peanuts", "gluten", "soy", 
                        "eggs", "fish", "shellfish", "coconut", "sesame"]
        allergen_vars = {}
        
        allergen_frame = tk.Frame(form_frame, bg="white")
        allergen_frame.pack(pady=10)
        
        for i, allergen in enumerate(allergen_list):
            var = tk.BooleanVar()
            allergen_vars[allergen] = var
            cb = tk.Checkbutton(
                allergen_frame,
                text=allergen.capitalize(),
                variable=var,
                font=("Arial", 10),
                bg="white"
            )
            cb.grid(row=i//3, column=i%3, sticky='w', padx=10, pady=2)
        
        # Health Score
        tk.Label(form_frame, text="Health Information", 
                font=("Arial", 14, "bold"), bg="white").pack(pady=(20, 10))
        create_field("Health Score (0-100)", "health_score", "50", "number")
        
        def save_product():
            """Save product to database via API"""
            # Validate required fields
            if not fields["name"].get().strip():
                messagebox.showerror("Error", "Product name is required!")
                return
            
            # Collect allergens
            selected_allergens = [allergen for allergen, var in allergen_vars.items() if var.get()]
            
            # Build product data
            try:
                product_data = {
                    "barcode": barcode,
                    "name": fields["name"].get().strip(),
                    "brand": fields["brand"].get().strip(),
                    "category": fields["category"].get().strip(),
                    "calories": float(fields["calories"].get() or 0),
                    "protein": float(fields["protein"].get() or 0),
                    "carbs": float(fields["carbs"].get() or 0),
                    "sugar": float(fields["sugar"].get() or 0),
                    "fats": float(fields["fats"].get() or 0),
                    "saturated_fats": float(fields["saturated_fats"].get() or 0),
                    "fiber": float(fields["fiber"].get() or 0),
                    "sodium": float(fields["sodium"].get() or 0),
                    "allergens": selected_allergens,
                    "health_score": int(fields["health_score"].get() or 50),
                    "is_healthy": 1 if int(fields["health_score"].get() or 50) >= 60 else 0
                }
            except ValueError as e:
                messagebox.showerror("Error", "Please enter valid numbers for nutrition values")
                return
            
            # Send to API
            try:
                response = requests.post(
                    f"{API_BASE_URL}/add_product.php",
                    json=product_data,
                    timeout=10
                )
                
                result = response.json()
                
                if result.get('success'):
                    # Also cache locally
                    self.cache_product(product_data)
                    
                    success_msg = f"Product '{product_data['name']}' added successfully!\n\n"
                    success_msg += f"Barcode: {barcode}\n"
                    if image_path:
                        success_msg += f"Image saved to: {image_path}"
                    
                    messagebox.showinfo("Success", success_msg)
                    form_window.destroy()
                    self.camera_label.config(image='', text="Camera Off", bg="black", fg="white")
                    
                    # Update statistics
                    self.total_scans = self.get_total_scans()
                    self.healthy_scans = self.get_healthy_scans()
                    self.allergen_warnings = self.get_allergen_warnings()
                    self.scan_counter_label.config(text=f"Total Scans: {self.total_scans}")
                else:
                    messagebox.showerror("Error", f"Failed to add product:\n\n{result.get('error')}")
            
            except Exception as e:
                messagebox.showerror("Error", f"Failed to connect to API:\n\n{str(e)}")
        
        # Buttons
        button_frame = tk.Frame(form_frame, bg="white")
        button_frame.pack(pady=30)
        
        tk.Button(
            button_frame,
            text="Save Product",
            command=save_product,
            bg="#4caf50",
            fg="white",
            font=("Arial", 14, "bold"),
            width=15,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            button_frame,
            text="Cancel",
            command=lambda: [form_window.destroy(), 
                            self.camera_label.config(image='', text="Camera Off", bg="black", fg="white")],
            bg="#757575",
            fg="white",
            font=("Arial", 14, "bold"),
            width=15,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
    
    def upload_image(self):
        """Upload image and scan for barcode"""
        print("INFO: Opening file dialog...")
        file_path = filedialog.askopenfilename(
            title="Select Barcode Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            print("INFO: No file selected")
            return
        
        print(f"INFO: Selected file: {file_path}")
        
        try:
            image = cv2.imread(file_path)
            
            if image is None:
                print("ERROR: Could not read image file")
                messagebox.showerror("Error", "Could not read image file.\nPlease select a valid image.")
                return
            
            print(f"SUCCESS: Image loaded: {image.shape}")
            
            # Display image in camera label
            display_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            display_pil = Image.fromarray(display_image)
            display_pil = display_pil.resize((480, 360), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
            display_tk = ImageTk.PhotoImage(display_pil)
            
            self.camera_label.config(image=display_tk, text="")
            self.camera_label.image = display_tk
            self.root.update()
            
            print("INFO: Decoding barcodes...")
            
            barcodes = pyzbar.decode(image)
            
            if barcodes:
                barcode_data = barcodes[0].data.decode('utf-8')
                print(f"SUCCESS: Barcode found: {barcode_data}")
                self.process_barcode(barcode_data)
            else:
                print("ERROR: No barcode detected in image")
                messagebox.showerror(
                    "No Barcode Found",
                    "No barcode detected in the image.\n\n" +
                    "Tips:\n" +
                    "- Ensure the barcode is clear and in focus\n" +
                    "- Try better lighting conditions\n" +
                    "- Use a higher resolution image\n" +
                    "- Make sure the entire barcode is visible"
                )
        
        except Exception as e:
            print(f"ERROR: Error processing image: {e}")
            messagebox.showerror("Error", f"Failed to process image:\n\n{str(e)}")
    
    def manual_entry(self):
        """Manual barcode entry to retrieve product information"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Manual Barcode Entry")
        dialog.geometry("400x180")
        dialog.configure(bg="white")
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text="Enter Barcode to Retrieve Info:",
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
            text="Search",
            command=submit,
            bg="#4caf50",
            fg="white",
            font=("Arial", 12, "bold"),
            width=15,
            height=2,
            cursor="hand2"
        )
        submit_btn.pack(pady=10)
        
        entry.bind('<Return>', lambda e: submit())
    
    def view_history(self):
        """View scan history"""
        history_window = tk.Toplevel(self.root)
        history_window.title("Scan History")
        history_window.geometry("700x600")
        history_window.configure(bg="white")
        
        tk.Label(
            history_window,
            text="Recent Scans",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=20)
        
        # Scrollable history
        canvas = tk.Canvas(history_window, bg="white")
        scrollbar = ttk.Scrollbar(history_window, orient="vertical", command=canvas.yview)
        history_frame = tk.Frame(canvas, bg="white")
        
        history_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=history_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        scrollbar.pack(side="right", fill="y")
        
        # Get history from database
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT sh.barcode, p.name, sh.scanned_at, sh.is_healthy, sh.has_allergen
            FROM scan_history sh
            LEFT JOIN products p ON sh.barcode = p.barcode
            ORDER BY sh.scanned_at DESC
            LIMIT 50
        ''')
        history = cursor.fetchall()
        conn.close()
        
        if not history:
            tk.Label(
                history_frame,
                text="No scan history yet!",
                font=("Arial", 12),
                bg="white",
                fg="#666"
            ).pack(pady=50)
        else:
            for i, (barcode, name, scanned_at, is_healthy, has_allergen) in enumerate(history):
                item_frame = tk.Frame(history_frame, bg="#f5f5f5", relief=tk.RAISED, bd=1)
                item_frame.pack(fill=tk.X, padx=10, pady=5)
                
                # Determine indicator
                indicator = "[HEALTHY]" if is_healthy else "[WARNING]"
                indicator_color = "#4caf50" if is_healthy else "#ff9800"
                if has_allergen:
                    indicator = "[ALLERGEN]"
                    indicator_color = "#f44336"
                
                indicator_label = tk.Label(
                    item_frame,
                    text=indicator,
                    font=("Arial", 10, "bold"),
                    bg="#f5f5f5",
                    fg=indicator_color,
                    width=12
                )
                indicator_label.pack(side=tk.LEFT, padx=5, pady=10)
                
                tk.Label(
                    item_frame,
                    text=f"{name or 'Unknown Product'} ({barcode})",
                    font=("Arial", 11),
                    bg="#f5f5f5",
                    anchor="w"
                ).pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)
                
                tk.Label(
                    item_frame,
                    text=scanned_at,
                    font=("Arial", 9),
                    bg="#f5f5f5",
                    fg="#666"
                ).pack(side=tk.RIGHT, padx=10, pady=10)
        
        tk.Button(
            history_window,
            text="Close",
            command=history_window.destroy,
            bg="#757575",
            fg="white",
            font=("Arial", 11),
            width=20,
            cursor="hand2"
        ).pack(pady=20)
    
    def view_statistics(self):
        """View scanning statistics"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Statistics")
        stats_window.geometry("600x550")
        stats_window.configure(bg="white")
        
        tk.Label(
            stats_window,
            text="Your Scanning Statistics",
            font=("Arial", 16, "bold"),
            bg="white"
        ).pack(pady=20)
        
        stats_frame = tk.Frame(stats_window, bg="white")
        stats_frame.pack(pady=20, padx=40, fill=tk.BOTH, expand=True)
        
        # Total scans
        total_frame = tk.Frame(stats_frame, bg="#e3f2fd", relief=tk.RAISED, bd=2)
        total_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            total_frame,
            text="Total Scans",
            font=("Arial", 14, "bold"),
            bg="#e3f2fd"
        ).pack(pady=10)
        
        tk.Label(
            total_frame,
            text=str(self.total_scans),
            font=("Arial", 32, "bold"),
            bg="#e3f2fd",
            fg="#2196f3"
        ).pack(pady=5)
        
        # Healthy products
        healthy_frame = tk.Frame(stats_frame, bg="#e8f5e9", relief=tk.RAISED, bd=2)
        healthy_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            healthy_frame,
            text="Healthy Products",
            font=("Arial", 14, "bold"),
            bg="#e8f5e9"
        ).pack(pady=10)
        
        healthy_percentage = (self.healthy_scans / self.total_scans * 100) if self.total_scans > 0 else 0
        
        tk.Label(
            healthy_frame,
            text=f"{self.healthy_scans} ({healthy_percentage:.1f}%)",
            font=("Arial", 28, "bold"),
            bg="#e8f5e9",
            fg="#4caf50"
        ).pack(pady=5)
        
        # Allergen warnings
        allergen_frame = tk.Frame(stats_frame, bg="#ffebee", relief=tk.RAISED, bd=2)
        allergen_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            allergen_frame,
            text="Allergen Warnings",
            font=("Arial", 14, "bold"),
            bg="#ffebee"
        ).pack(pady=10)
        
        tk.Label(
            allergen_frame,
            text=str(self.allergen_warnings),
            font=("Arial", 32, "bold"),
            bg="#ffebee",
            fg="#f44336"
        ).pack(pady=5)
        
        # LED animations (if SenseHat available)
        if SENSEHAT_AVAILABLE:
            tk.Label(
                stats_window,
                text="Test LED Animations:",
                font=("Arial", 12),
                bg="white"
            ).pack(pady=(20, 10))
            
            led_frame = tk.Frame(stats_window, bg="white")
            led_frame.pack()
            
            tk.Button(
                led_frame,
                text="Rainbow",
                command=lambda: self.set_led_color(None, 'rainbow'),
                bg="#9c27b0",
                fg="white",
                font=("Arial", 10),
                width=10,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                led_frame,
                text="Pulse",
                command=lambda: self.set_led_color(GREEN, 'pulse'),
                bg="#4caf50",
                fg="white",
                font=("Arial", 10),
                width=10,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Button(
                led_frame,
                text="Flash",
                command=lambda: self.set_led_color(RED, 'flash'),
                bg="#f44336",
                fg="white",
                font=("Arial", 10),
                width=10,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            stats_window,
            text="Close",
            command=stats_window.destroy,
            bg="#757575",
            fg="white",
            font=("Arial", 11),
            width=20,
            cursor="hand2"
        ).pack(pady=20)
    
    def process_barcode(self, barcode):
        """Process barcode - removes leading 0 for UPC-A codes and retrieves product"""
        # Convert EAN-13 to UPC-A if needed
        if len(barcode) == 13 and barcode.startswith('0'):
            barcode = barcode[1:]
        
        print(f"INFO: Processing barcode: {barcode}")
        
        # Clear results frame
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading = tk.Label(
            self.results_frame,
            text="Loading product information...",
            font=("Arial", 16),
            bg="white"
        )
        loading.pack(pady=50)
        self.root.update()
        
        # Get product data
        product = self.get_product_data(barcode)
        
        if product:
            self.display_product_info(product)
            
            # Update statistics
            self.total_scans = self.get_total_scans()
            self.healthy_scans = self.get_healthy_scans()
            self.allergen_warnings = self.get_allergen_warnings()
            self.scan_counter_label.config(text=f"Total Scans: {self.total_scans}")
        else:
            self.display_error(f"Product not found: {barcode}")
            if SENSEHAT_AVAILABLE:
                self.set_led_color(OFF)
    
    def get_product_data(self, barcode):
        """Get product from API or cache"""
        product = None
        
        if self.is_online:
            try:
                print(f"INFO: API call: {API_BASE_URL}/get_product.php?barcode={barcode}")
                response = requests.get(
                    f"{API_BASE_URL}/get_product.php?barcode={barcode}",
                    timeout=5
                )
                
                print(f"INFO: Response: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        product = data.get('data')
                        self.cache_product(product)
                        print(f"SUCCESS: Fetched from database: {product['name']}")
                    else:
                        print(f"INFO: Product not found in API: {data.get('error')}")
                else:
                    print(f"ERROR: HTTP error: {response.status_code}")
            except Exception as e:
                print(f"ERROR: API Error: {e}")
        
        # If not found online or offline mode, check cache
        if not product:
            product = self.get_cached_product(barcode)
            if product:
                print(f"SUCCESS: Loaded from cache: {product['name']}")
        
        return product
    
    def cache_product(self, product):
        """Cache product in local database"""
        conn = sqlite3.connect(SQLITE_DB)
        cursor = conn.cursor()
        
        # Handle allergens - convert list to string for storage
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
        
        # Check if product has user's allergens
        product_allergens = set(product.get('allergens', []))
        if isinstance(product.get('allergens'), str):
            product_allergens = set(product['allergens'].split(',')) if product['allergens'] else set()
        has_allergen = 1 if bool(self.user_allergens & product_allergens) else 0
        
        # Add to scan history
        cursor.execute(
            'INSERT INTO scan_history (barcode, is_healthy, has_allergen) VALUES (?, ?, ?)', 
            (product['barcode'], product.get('is_healthy', 0), has_allergen)
        )
        conn.commit()
        conn.close()
    
    def get_cached_product(self, barcode):
        """Get product from local cache"""
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
            
            # Convert allergens string back to list
            if product['allergens']:
                product['allergens'] = product['allergens'].split(',')
            else:
                product['allergens'] = []
            
            return product
        
        return None
    
    def display_product_info(self, product):
        """Display product information in results panel"""
        # Clear results frame
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Check for allergens
        product_allergens = set(product.get('allergens', []))
        if isinstance(product.get('allergens'), str):
            product_allergens = set(product['allergens'].split(',')) if product['allergens'] else set()
        
        has_allergen = bool(self.user_allergens & product_allergens)
        
        # Set LED color based on product status
        if SENSEHAT_AVAILABLE:
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
        
        # Brand
        if product.get('brand'):
            brand_label = tk.Label(
                self.results_frame,
                text=product['brand'],
                font=("Arial", 12),
                bg="white",
                fg="#666"
            )
            brand_label.pack()
        
        # Allergen warning (if applicable)
        if has_allergen:
            allergen_frame = tk.LabelFrame(
                self.results_frame,
                text="⚠️ ALLERGEN ALERT",
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
                text=f"WARNING: Contains {allergens_text}",
                font=("Arial", 12, "bold"),
                bg="#ffebee",
                fg="#f44336",
                wraplength=350
            ).pack(padx=10, pady=10)
        
        # Health Score
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
        
        # Health status
        if product.get('is_healthy'):
            health_text = "✓ Healthy Choice"
            health_color = "#4caf50"
        else:
            health_text = "⚠️ Consider Healthier Options"
            health_color = "#ff9800"
        
        tk.Label(
            self.results_frame,
            text=health_text,
            font=("Arial", 12, "bold"),
            bg="white",
            fg=health_color
        ).pack(pady=5)
        
        # Nutrition facts
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
            ("Carbohydrates", product.get('carbs'), "g"),
            ("Sugar", product.get('sugar'), "g"),
            ("Total Fat", product.get('fats'), "g"),
            ("Saturated Fat", product.get('saturated_fats'), "g"),
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
        
        # All allergens in product
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
        
        # Category
        if product.get('category'):
            tk.Label(
                self.results_frame,
                text=f"Category: {product['category']}",
                font=("Arial", 10),
                bg="white",
                fg="#666"
            ).pack(pady=5)
    
    def display_error(self, message):
        """Display error message in results panel"""
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        error_label = tk.Label(
            self.results_frame,
            text="Product Not Found",
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
        
        # Suggestions
        suggestions = tk.Label(
            self.results_frame,
            text="Try:\n• Adding the product using 'Add Product' button\n• Checking the barcode number\n• Using Manual Entry",
            font=("Arial", 11),
            bg="white",
            fg="#666",
            justify=tk.LEFT
        )
        suggestions.pack(pady=20)


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = NutritionScannerApp(root)
    
    try:
        root.mainloop()
    finally:
        if SENSEHAT_AVAILABLE:
            sense.clear()
        print("INFO: Application closed")


if __name__ == "__main__":
    main()