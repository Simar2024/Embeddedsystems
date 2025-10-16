<?php
// Database configuration for db4free.net
define('DB_HOST', 'db4free.net');
define('DB_USER', 'paramdatabase');      // ← CORRECTED!
define('DB_PASS', '12345678');
define('DB_NAME', 'smartscanner1');      // ← CORRECTED!
define('DB_PORT', '3306');

// Function to get database connection
function getConnection() {
    $conn = new mysqli(DB_HOST, DB_USER, DB_PASS, DB_NAME, DB_PORT);
    
    if ($conn->connect_error) {
        http_response_code(500);
        die(json_encode([
            "success" => false,
            "error" => "Database connection failed",
            "message" => $conn->connect_error
        ]));
    }
    
    $conn->set_charset("utf8mb4");
    return $conn;
}

// CORS headers for API access
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE");
header("Access-Control-Allow-Headers: Content-Type");
header("Content-Type: application/json; charset=UTF-8");
?>