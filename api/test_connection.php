<?php
require_once 'config.php';

try {
    $conn = getConnection();
    
    $result = $conn->query("SELECT COUNT(*) as total FROM products");
    $stats = $result->fetch_assoc();
    
    $result2 = $conn->query("SELECT COUNT(*) as scans FROM scan_history");
    $scans = $result2->fetch_assoc();
    
    http_response_code(200);
    echo json_encode([
        "success" => true,
        "message" => "Database connection successful",
        "stats" => [
            "total_products" => $stats['total'],
            "total_scans" => $scans['scans']
        ],
        "timestamp" => date('Y-m-d H:i:s')
    ]);
    
    $conn->close();
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        "success" => false,
        "error" => "Connection failed",
        "message" => $e->getMessage()
    ]);
}
?>