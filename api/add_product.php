<?php
require_once 'config.php';

header("Content-Type: application/json");

$data = json_decode(file_get_contents('php://input'), true);

if (!isset($data['barcode']) || !isset($data['name'])) {
    http_response_code(400);
    echo json_encode([
        "success" => false,
        "error" => "Barcode and name are required"
    ]);
    exit();
}

$conn = getConnection();

$stmt = $conn->prepare("
    INSERT INTO products 
    (barcode, name, brand, category, calories, protein, carbs, sugar, fats, 
     saturated_fats, fiber, sodium, allergens, health_score, is_healthy)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    brand = VALUES(brand),
    category = VALUES(category),
    calories = VALUES(calories),
    protein = VALUES(protein),
    carbs = VALUES(carbs),
    sugar = VALUES(sugar),
    fats = VALUES(fats),
    saturated_fats = VALUES(saturated_fats),
    fiber = VALUES(fiber),
    sodium = VALUES(sodium),
    allergens = VALUES(allergens),
    health_score = VALUES(health_score),
    is_healthy = VALUES(is_healthy)
");

$allergens_str = '';
if (isset($data['allergens']) && is_array($data['allergens'])) {
    $allergens_str = implode(',', $data['allergens']);
} elseif (isset($data['allergens'])) {
    $allergens_str = $data['allergens'];
}

$stmt->bind_param(
    "ssssddddddddsdi",
    $data['barcode'],
    $data['name'],
    $data['brand'] ?? '',
    $data['category'] ?? '',
    $data['calories'] ?? 0,
    $data['protein'] ?? 0,
    $data['carbs'] ?? 0,
    $data['sugar'] ?? 0,
    $data['fats'] ?? 0,
    $data['saturated_fats'] ?? 0,
    $data['fiber'] ?? 0,
    $data['sodium'] ?? 0,
    $allergens_str,
    $data['health_score'] ?? 50,
    $data['is_healthy'] ?? 0
);

if ($stmt->execute()) {
    http_response_code(201);
    echo json_encode([
        "success" => true,
        "message" => "Product added successfully",
        "barcode" => $data['barcode']
    ]);
} else {
    http_response_code(500);
    echo json_encode([
        "success" => false,
        "error" => "Failed to add product",
        "details" => $stmt->error
    ]);
}

$stmt->close();
$conn->close();
?>