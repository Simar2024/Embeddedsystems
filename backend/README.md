# Backend - PHP API

This directory contains the PHP backend API for the Smart Barcode Nutrition Scanner.

## Files

- **`getProduct.php`** - Retrieves a single product by barcode
- **`getAllProducts.php`** - Retrieves all products for cache synchronization
- **`test.php`** - Simple test file

## Setup

### 1. LAMP Stack Installation

#### On Linux/Raspberry Pi:
```bash
sudo apt-get update
sudo apt-get install -y apache2 mysql-server php php-mysql libapache2-mod-php
```

### 2. Database Setup

```sql
CREATE DATABASE smartscanner;
CREATE USER 'smartuser'@'localhost' IDENTIFIED BY 'password123';
GRANT ALL PRIVILEGES ON smartscanner.* TO 'smartuser'@'localhost';
FLUSH PRIVILEGES;

USE smartscanner;

CREATE TABLE products (
    barcode VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    calories INT,
    fat FLOAT,
    protein FLOAT,
    carbs FLOAT,
    allergens VARCHAR(255),
    healthier_alternative VARCHAR(255),
    fiber FLOAT DEFAULT 0,
    sugar FLOAT DEFAULT 0,
    sodium FLOAT DEFAULT 0
);
```

### 3. Deploy PHP Files

Copy these files to your web server directory:
```bash
# On Raspberry Pi/Linux
sudo cp *.php /var/www/html/smartscanner/
sudo chown -R www-data:www-data /var/www/html/smartscanner/
sudo chmod 755 /var/www/html/smartscanner/*.php
```

### 4. Test API

```bash
# Test connection
curl http://localhost/smartscanner/test.php

# Test product retrieval
curl "http://localhost/smartscanner/getProduct.php?barcode=1234567890"

# Test all products
curl http://localhost/smartscanner/getAllProducts.php
```

## API Endpoints

### GET /getProduct.php?barcode={barcode}

Retrieves a single product by barcode.

**Parameters:**
- `barcode` (string, required) - The product barcode

**Response:**
```json
{
  "barcode": "1234567890",
  "name": "Organic Whole Wheat Bread",
  "calories": 250,
  "fat": 3.0,
  "protein": 8.0,
  "carbs": 45.0,
  "allergens": "gluten,wheat",
  "healthier_alternative": "Multigrain Bread",
  "fiber": 6.0,
  "sugar": 4.0,
  "sodium": 380.0
}
```

**Error Response:**
```json
{
  "error": "Product not found"
}
```

### GET /getAllProducts.php

Retrieves all products from the database.

**Response:**
```json
[
  {
    "barcode": "1234567890",
    "name": "Organic Whole Wheat Bread",
    ...
  },
  ...
]
```

## Configuration

Edit the database credentials in both PHP files:

```php
$servername = "localhost";
$username = "smartuser";
$password = "password123";
$dbname = "smartscanner";
```

## Security Notes

- Change default database password in production
- Use HTTPS in production
- Implement rate limiting
- Add input validation
- Use prepared statements (already implemented)
- Consider adding API authentication

## Troubleshooting

### "Connection refused"
- Check if Apache is running: `sudo systemctl status apache2`
- Start Apache: `sudo systemctl start apache2`

### "Access denied for user"
- Verify MySQL credentials
- Check user permissions: `SHOW GRANTS FOR 'smartuser'@'localhost';`

### "500 Internal Server Error"
- Check PHP error logs: `sudo tail -f /var/log/apache2/error.log`
- Verify file permissions
- Check PHP syntax: `php -l getProduct.php`
