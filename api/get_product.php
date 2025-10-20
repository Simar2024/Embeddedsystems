<?php
require_once 'config.php';

if (!isset($_GET['barcode']) || empty($_GET['barcode'])) {
    http_response_code(400);
    echo json_encode([
        "success" => false,
        "error" => "Missing barcode parameter"
    ]);
    exit();
}

$barcode = $_GET['barcode'];
$conn = getConnection();

$stmt = $conn->prepare("SELECT * FROM products WHERE barcode = ?");
$stmt->bind_param("s", $barcode);
$stmt->execute();
$result = $stmt->get_result();

if ($result->num_rows > 0) {
    $product = $result->fetch_assoc();
   
    if ($product['allergens']) {
        $product['allergens'] = array_map('trim', explode(',', $product['allergens']));
    } else {
        $product['allergens'] = [];
    }
   
    $log_stmt = $conn->prepare("INSERT INTO scan_history (barcode) VALUES (?)");
    $log_stmt->bind_param("s", $barcode);
    $log_stmt->execute();
    $log_stmt->close();
   
    http_response_code(200);
    echo json_encode([
        "success" => true,
        "data" => $product
    ]);
} else {
    http_response_code(404);
    echo json_encode([
        "success" => false,
        "error" => "Product not found",
        "barcode" => $barcode
    ]);
}

$stmt->close();
$conn->close();
?>
