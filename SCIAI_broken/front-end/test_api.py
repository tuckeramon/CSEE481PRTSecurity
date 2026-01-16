from models.api import send_cart_to_station

if __name__ == "__main__":
    # Test values
    test_cart_id = "TEST123"
    test_station_id = "Station 1"

    print(f"Sending cart {test_cart_id} to station {test_station_id}...")
    result = send_cart_to_station(test_cart_id, test_station_id)
    print("Operation completed. Check your database and API logs for results.")
