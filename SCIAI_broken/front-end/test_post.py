import requests

# Test GET /log_event endpoint
BASE_URL = "http://localhost:5000/log_event"

def test_log_event(cart_id, position, status, transaction_id=None):
    params = {
        "cart_id": cart_id,
        "position": position,
        "status": status,
        "transaction_id": transaction_id or ""
    }
    response = requests.get(BASE_URL, params=params)
    print(f"Request URL: {response.url}")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    print("Testing with transaction_id=None (should log as 'Report'):")
    test_log_event("0009", "Station_1", "active", None)

    print("\nTesting with transaction_id set (should log as 'Request'):")
    test_log_event("0006", "Station_2", "inactive", "TXN001")
