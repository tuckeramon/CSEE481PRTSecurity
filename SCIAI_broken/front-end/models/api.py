import requests
from models.db import get_connection, remove_cart_request
import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/prt/dest', methods=['POST'])
def send_cart_to_station(cart_id, station_id):
    """
    Send a request to the API to move a cart to a specific station.
    """
    station_map = {
        "Station_1": 1,
        "Station_2": 2,
        "Station_3": 3,
        "Station_4": 4
    }
    destination = station_map.get(station_id)
    api_url = "http://localhost:2650/prt/dest"
    payload = {
        "barcode": cart_id,
        "destination": destination
    }

    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO cart_logs (cart_id, position, event, time_stamp)
                VALUES (%s, %s, %s, %s)"""
            data = (cart_id, station_id, 'sent', datetime.datetime.now())
            cursor.execute(query, data)
            conn.commit()

            cursor.close()
            conn.close()
        else:
            conn = get_connection()
            cursor = conn.cursor()

            query = """
                INSERT INTO cart_logs (cart_id, position, event, time_stamp)
                VALUES (%s, %s, %s, %s)"""
            data = (cart_id, station_id, 'error', datetime.datetime.now())
            cursor.execute(query, data)
            conn.commit()

            cursor.close()
            conn.close()
    except requests.RequestException as e:
        print(f"Error connecting to API: {e}")

@app.route('/prt/remove', methods=['POST'])
def remove_cart(cart_id, area):
    """
    Remove a cart from the conveyor system.
    """
    api_url = "http://localhost:2650/prt/remove"
    payload = {
        "barcode": cart_id,
        "area": area
    }
    try:
        response = requests.post(api_url, json=payload)
        if response.status_code == 200:
            remove_cart_request(cart_id, area)
    except requests.RequestException as e:
        print(f"Error connecting to API: {e}")
        
