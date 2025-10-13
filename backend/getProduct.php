<?php
header("Content-Type: application/json");

$servername = "localhost";
$username = "smartuser";
$password = "password123";
$dbname = "smartscanner";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die(json_encode(["error" => "Database connection failed"]));
}

if (!isset($_GET['barcode'])) {
    echo json_encode(["error" => "No barcode provided"]);
    exit();
}

$barcode = $conn->real_escape_string($_GET['barcode']);
$sql = "SELECT * FROM products WHERE barcode='$barcode'";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    echo json_encode($result->fetch_assoc());
} else {
    echo json_encode(["error" => "Product not found"]);
}

$conn->close();
?>
