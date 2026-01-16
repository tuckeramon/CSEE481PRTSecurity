from time import time, sleep
from Communication.PLC import PLC
from Communication.PRTDB import PRTDB
from DataCollection.DataLogger import DataLogger
from PRTConfig import TAG_TO_READ, STATUS_BIT, TAG_TO_WRITE, prt_get_dest_route
from Communication.PLCConfig import PRT_PLC_IP_ADDRESS
from PRTPLC import PRTPLC
from PRTConfig import BARCODE_DESTINATION_MAP
from Server import Server
from threading import Thread

# Data Logger
logger = DataLogger('datalogs', 'dataplots')
# Data save interval (seconds), last save time
SAVE_INTERVAL = 60

# Watchdog interval (seconds)
WATCHDOG_INTERVAL = 2

# PRT PLC
prt = None
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'prtdb'
}
prtdb = PRTDB(config)
server = None

def get_destination(barcode: str, sorter_num: int):
    print(f"GET_DEST: barcode: {barcode}, sorter_num: {sorter_num}")
    #physical_dest = BARCODE_DESTINATION_MAP.get(barcode)  # Stations 1-4
    barcode, physical_dest = prtdb.get_destination_info(barcode)  # Stations 1-4
    dest_rt = prt_get_dest_route(physical_dest)
    dest = dest_rt[sorter_num]
    print(f"GET_DEST: barcode: {barcode}, sorter_num: {sorter_num}, physical_dest: {physical_dest}, dest_rt: {dest_rt}, dest: {dest}")
    return prt_get_dest_route(physical_dest)[sorter_num]

def process_barcode(barcode: str):
    if len(barcode) != 4:
        return "0000"
    elif barcode[0] < '0' or barcode[0] > '9':
        return "0000"
    elif barcode[1] < '0' or barcode[1] > '9':
        return "0000"
    elif barcode[2] < '0' or barcode[2] > '9':
        return "0000"
    elif barcode[3] < '0' or barcode[3] > '9':
        return "0000"
    return barcode

def initialize_system():
    print(f"PRT_PLC: Connecting to PLC: {PRT_PLC_IP_ADDRESS}...")
    global prt, server
    prt = PRTPLC()
    # Create the Flask server with the connected PLC instance
    server = Server(prtdb, prt)
    prt.write_tag(f'SORTER_1_REQUEST.END', 0)
    prt.write_tag(f'SORTER_2_REQUEST.END', 0)
    prt.write_tag(f'SORTER_1_REPORT.END', 0)
    prt.write_tag(f'SORTER_2_REPORT.END', 0)
    prt.send_watchdog_signal()
    flask_thread = Thread(target=server.start_flask_server)
    flask_thread.daemon = True
    flask_thread.start()

def run_system():
    initialize_system()
    LAST_SAVE_TIME = time()
    LAST_WATCHDOG_TIME = time()
    while (True):
        process_sorter(1)
        process_sorter(2)
        current_time = time()
        if current_time - LAST_SAVE_TIME >= SAVE_INTERVAL:
            logger.save_log("PRT")
            LAST_SAVE_TIME = current_time
        if current_time - LAST_WATCHDOG_TIME >= WATCHDOG_INTERVAL:
            prt.send_watchdog_signal()
            LAST_WATCHDOG_TIME = current_time

def process_sorter(sorter_num: int):
    sorter_request = prt.read_sorter_request(sorter_num)
    if sorter_request is not None:
        print(f'Sorter_Request: {sorter_request}')
        barcode, transaction_id = sorter_request
        # Add handling for when barcode is invalid-Send it straight, log an error
        barcode = process_barcode(barcode)
        #logger.log_data(SORTER=sorter_num, TYPE="REQUEST", TRANSACTION_ID=transaction_id, BARCODE=barcode)
        prtdb.store_sorter_request(sorter_num, barcode, transaction_id)
        destination = get_destination(barcode, sorter_num)
        prt.send_sorter_response(sorter_num, transaction_id, destination)
        #logger.log_data(SORTER=sorter_num, TYPE="RESPONSE", TRANSACTION_ID=transaction_id, DESTINATION=destination)
        prtdb.store_sorter_response(sorter_num, transaction_id, barcode, destination)

    sorter_report = prt.read_sorter_report(sorter_num)
    if sorter_report is not None:
        barcode, active, lost, good, diverted = sorter_report
        #logger.log_data(SORTER=sorter_num, TYPE="REPORT", BARCODE=barcode, ACTIVE=active, LOST=lost, GOOD=good, DIVERTED=diverted)
        barcode = process_barcode(barcode)
        prtdb.store_sorter_report(sorter_num, barcode, active, lost, good, diverted)


def tes_system():
    print(f"PLCPrt: Connecting to PLC: {PRT_PLC_IP_ADDRESS}...")
    prt_plc = PLC(PRT_PLC_IP_ADDRESS)
    prt_plc.connect()
    print(f"PLCPrt: Successfully connected to PLC: {PRT_PLC_IP_ADDRESS}...")
    while (True):
        end_bit = prt_plc.read_tag(TAG_TO_READ + STATUS_BIT)
        print(f"End bit: {end_bit}")
        if end_bit == 1:
            data = prt_plc.read_tag(TAG_TO_READ)
            print(f"Data: {data}")
            prt_plc.write_tag(TAG_TO_READ + STATUS_BIT, 0)
            prt_plc.write_tag(TAG_TO_WRITE + '.TRANSACTION_ID', data['TRANSACTION_ID'])
            prt_plc.write_tag(TAG_TO_WRITE + '.DESTINATION', 2)
            prt_plc.write_tag(TAG_TO_WRITE + '.END', 1)
            
        
def main():
    run_system()
    #test_system()

if __name__ == "__main__":
    main()