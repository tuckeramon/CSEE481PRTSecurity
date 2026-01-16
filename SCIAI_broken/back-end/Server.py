from flask import Flask, request, jsonify
from Communication.PRTDB import PRTDB
from PRTPLC import PRTPLC

class Server:
    def __init__(self, prtdb: PRTDB, prtplc: PRTPLC):
        self.prtdb = prtdb
        self.prtplc = prtplc
        self.app = Flask(__name__)
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/prt/dest', methods=['POST'])
        def update_prt_destination():
            data = request.get_json()
            barcode = data.get('barcode')
            destination = data.get('destination')

            if not barcode or destination is None:
                return jsonify({'error': 'Missing barcode or destination'}), 400

            success = self.prtdb.update_destination_info(barcode, destination)
            if success:
                return jsonify({'message': f'Destination for {barcode} set to {destination}'}), 200
            else:
                return jsonify({'error': 'Database write failed'}), 500

        @self.app.route('/prt/dest', methods=['GET'])
        def get_prt_destinations():
            destinations = self.prtdb.get_destination_info()
            return jsonify(destinations), 200

        @self.app.route('/prt/remove', methods=['POST'])
        def remove_cart():
            data = request.get_json()
            barcode = data.get('barcode')
            area = int(data.get('area'))

            if not barcode or not area:
                return jsonify({'error': 'Missing barcode or area'}), 400
            success = self.prtdb.update_destination_info(barcode, area)
            if success:
                return jsonify({'message': f'Cart {barcode} removed to area {area}'}), 200
            else:
                return jsonify({'error': 'Database write failed'}), 500
            
    def start_flask_server(self, host='0.0.0.0', port=2650):
        self.app.run(host=host, port=port)
