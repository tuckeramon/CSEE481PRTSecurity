from time import time
from Communication.PLC import PLC
from Communication.PLCConfig import PRT_PLC_IP_ADDRESS

# Debug logging interval: print "no data" messages at most once every N seconds
# to avoid flooding the console during normal polling
DEBUG_LOG_INTERVAL = 5

class PRTPLC(PLC):
    """
    Represents the PRT PLC
    """
    def __init__(self):
        super().__init__(PRT_PLC_IP_ADDRESS)
        self._last_debug_time = {1: 0, 2: 0}
        connected = self.connect()
        if connected:
            print(f"DEBUG PRT_PLC: Successfully connected to PLC at {PRT_PLC_IP_ADDRESS}")
        else:
            print(f"DEBUG PRT_PLC: FAILED to connect to PLC at {PRT_PLC_IP_ADDRESS} - driver is None")

    def read_sorter_request(self, sorter_num: int):
        data = self.read_tag(f'SORTER_{sorter_num}_REQUEST')
        now = time()

        if data is None:
            if now - self._last_debug_time.get(sorter_num, 0) >= DEBUG_LOG_INTERVAL:
                print(f"DEBUG SORTER_{sorter_num}_REQUEST: read_tag returned None (PLC not connected or read failed)")
                self._last_debug_time[sorter_num] = now
            return None

        if data['END'] == 1:
            raw_barcode = data['BARCODE']
            # Normalize barcode: strip null chars, carriage returns, newlines, and whitespace
            # Sorter 1 scanner appends \r which garbles the barcode (e.g., '9\r00' instead of '0009')
            if isinstance(raw_barcode, str):
                barcode = raw_barcode.strip('\x00').strip('\r\n').strip()
            else:
                barcode = str(raw_barcode).strip('\x00').strip('\r\n').strip()
            # Zero-pad to 4 digits if we got a short barcode after stripping
            barcode = barcode.zfill(4) if barcode else raw_barcode

            print(f"SORTER_REQUEST_{sorter_num}: END: 1, raw_barcode: {repr(raw_barcode)}, cleaned: {barcode}, transaction_id: {data['TRANSACTION_ID']}")
            #Clear tag
            self.write_tag(f'SORTER_{sorter_num}_REQUEST.END', 0)
            return barcode, data['TRANSACTION_ID']
        else:
            if now - self._last_debug_time.get(sorter_num, 0) >= DEBUG_LOG_INTERVAL:
                print(f"DEBUG SORTER_{sorter_num}_REQUEST: PLC connected, END={data['END']} (waiting for request), data={data}")
                self._last_debug_time[sorter_num] = now
            return None

    def send_sorter_response(self, sorter_num: int, transaction_id: int, destination: int):
        #Write response tags
        self.write_tag(f'SORTER_{sorter_num}_RESPONSE.TRANSACTION_ID', transaction_id)
        self.write_tag(f'SORTER_{sorter_num}_RESPONSE.DESTINATION', destination)
        self.write_tag(f'SORTER_{sorter_num}_RESPONSE.END', 1)
        print(f"SORTER_{sorter_num}_RESPONSE: TRANS_ID: {transaction_id}, DEST: {destination}")

    def read_sorter_report(self, sorter_num: int):
        report_key = sorter_num + 10  # use offset keys to avoid collision with request debug timers
        data = self.read_tag(f'SORTER_{sorter_num}_REPORT')
        now = time()

        if data is None:
            if now - self._last_debug_time.get(report_key, 0) >= DEBUG_LOG_INTERVAL:
                print(f"DEBUG SORTER_{sorter_num}_REPORT: read_tag returned None (PLC not connected or read failed)")
                self._last_debug_time[report_key] = now
            return None

        if data['END'] == 1:
            #Reset to 0
            self.write_tag(f'SORTER_{sorter_num}_REPORT.END', 0)
            raw_barcode = data.get('BARCODE', '')
            # Normalize barcode: strip null chars and whitespace (PLC often uses fixed-length fields filled with \x00)
            if isinstance(raw_barcode, str):
                barcode = raw_barcode.strip('\x00').strip()
            else:
                barcode = str(raw_barcode).strip('\x00').strip()

            # Only log and return when the scanner actually read a barcode (non-empty after normalization)

            if barcode:
                print(f"Sorted_Report: {data}")
                return barcode, data['FLAGS']['ACTIVE'], data['FLAGS']['LOST'], data['FLAGS']['GOOD'], data['FLAGS']['DIVERTED']

            print(f"DEBUG SORTER_{sorter_num}_REPORT: END=1 but barcode empty after normalization, raw='{raw_barcode}'")
            # Treat null/empty barcode as no report
            return None
        else:
            if now - self._last_debug_time.get(report_key, 0) >= DEBUG_LOG_INTERVAL:
                print(f"DEBUG SORTER_{sorter_num}_REPORT: PLC connected, END={data['END']} (no report), data={data}")
                self._last_debug_time[report_key] = now
            return None

    def send_watchdog_signal(self):
        self.write_tag('OPC_WATCHDOG', 1)
