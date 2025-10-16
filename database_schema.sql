-- Smart Barcode Nutrition Scanner - MySQL Database Schema
-- Database: smartscanner
-- For RemoteMySQL or any MySQL hosting

CREATE DATABASE IF NOT EXISTS smartscanner;
USE smartscanner;

-- Products table with nutrition information
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255),
    category VARCHAR(100),
    
    -- Nutrition Information (per 100g/ml)
    calories INT,
    protein DECIMAL(5,2),
    carbs DECIMAL(5,2),
    sugar DECIMAL(5,2),
    fats DECIMAL(5,2),
    saturated_fats DECIMAL(5,2),
    fiber DECIMAL(5,2),
    sodium DECIMAL(5,2),
    
    -- Allergen Information (comma-separated)
    allergens TEXT,
    
    -- Health Information
    health_score INT DEFAULT 50,
    is_healthy BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_barcode (barcode),
    INDEX idx_health_score (health_score),
    INDEX idx_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Scan History table
CREATE TABLE IF NOT EXISTS scan_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barcode VARCHAR(50) NOT NULL,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_barcode (barcode),
    INDEX idx_scanned_at (scanned_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert YOUR 3 Products for Demo

-- Product 1: NUT BAR (Healthy but contains nuts)
INSERT INTO products (
    barcode, name, brand, category, 
    calories, protein, carbs, sugar, fats, saturated_fats, fiber, sodium,
    allergens, health_score, is_healthy
) VALUES (
    '096619036530',
    'NUT BAR',
    'Healthy Snacks Co.',
    'Snacks',
    250, 8.5, 30.0, 12.0, 12.0, 2.0, 5.0, 0.15,
    'nuts',
    85,
    TRUE
);

-- Product 2: Chocolate Coconut Nut Bar (Unhealthy, contains coconut)
INSERT INTO products (
    barcode, name, brand, category,
    calories, protein, carbs, sugar, fats, saturated_fats, fiber, sodium,
    allergens, health_score, is_healthy
) VALUES (
    '637480324618',
    'Chocolate Coconut Nut Bar',
    'Sweet Treats Ltd.',
    'Confectionery',
    480, 5.2, 58.0, 45.0, 25.0, 15.0, 2.0, 0.25,
    'coconut,nuts,dairy',
    25,
    FALSE
);

-- Product 3: Demo/Search Test Product (Safe and healthy)
INSERT INTO products (
    barcode, name, brand, category,
    calories, protein, carbs, sugar, fats, saturated_fats, fiber, sodium,
    allergens, health_score, is_healthy
) VALUES (
    '123456',
    'Demo Healthy Product',
    'Test Brand',
    'Demo',
    120, 5.0, 20.0, 5.0, 3.0, 0.5, 4.0, 0.10,
    '',
    90,
    TRUE
);

-- Verify data
SELECT * FROM products;
SELECT COUNT(*) as total_products FROM products;