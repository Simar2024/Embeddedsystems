# In main.py, line ~400:
response = requests.get(
    f"{API_BASE_URL}/get_product.php?barcode={barcode}",
    timeout=5
)