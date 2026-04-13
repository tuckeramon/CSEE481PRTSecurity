from flask import Flask, jsonify, request, send_from_directory, make_response
import os

app = Flask(__name__, static_folder='.', static_url_path='')

from models.db import (
    fetch_all_carts, fetch_activity_logs, get_cart_info,
    fetch_security_logs, fetch_security_alerts, fetch_security_summary_stats,
    fetch_all_cart_ids
)
from models.api import send_cart_to_station, remove_cart


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/carts', methods=['GET'])
def get_carts():
    return jsonify(fetch_all_carts())


@app.route('/api/cart/<cart_id>', methods=['GET'])
def get_cart(cart_id):
    result = get_cart_info(cart_id)
    return jsonify(result) if result else ('', 404)


@app.route('/api/cart/<cart_id>/destination', methods=['POST'])
def set_destination(cart_id):
    data = request.json
    station = data.get('station')
    success = send_cart_to_station(cart_id, station)
    return jsonify({'success': success})


@app.route('/api/cart/<cart_id>/remove', methods=['POST'])
def remove_cart_api(cart_id):
    data = request.json
    area = data.get('area', 5)
    success = remove_cart(cart_id, area)
    return jsonify({'success': success})


@app.route('/api/logs', methods=['GET'])
def get_logs():
    limit = request.args.get('limit', 100, type=int)
    return jsonify(fetch_activity_logs(limit))


@app.route('/api/security/logs', methods=['GET'])
def get_security_logs():
    return jsonify(fetch_security_logs(limit=100))


@app.route('/api/security/alerts', methods=['GET'])
def get_security_alerts():
    return jsonify(fetch_security_alerts(limit=50))


@app.route('/api/security/summary', methods=['GET'])
def get_security_summary():
    return jsonify(fetch_security_summary_stats())


@app.route('/api/cart_ids', methods=['GET'])
def get_cart_ids():
    return jsonify(fetch_all_cart_ids())


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)