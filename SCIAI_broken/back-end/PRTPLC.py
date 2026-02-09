from Communication.PLC import PLC
from Communication.PLCConfig import PRT_PLC_IP_ADDRESS

class PRTPLC(PLC):
    """
    Represents the PRT PLC
    """
    def __init__(self):
        super().__init__(PRT_PLC_IP_ADDRESS)
        self.connect()

    def read_sorter_request(self, sorter_num: int):
        data = self.read_tag(f'SORTER_{sorter_num}_REQUEST')
        if data is None:
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

            print(f"SORTER_REQUEST_{sorter_num}: END: 1, barcode: {barcode}, transaction_id: {data['TRANSACTION_ID']}")
            #Clear tag
            self.write_tag(f'SORTER_{sorter_num}_REQUEST.END', 0)
            return barcode, data['TRANSACTION_ID']

    def send_sorter_response(self, sorter_num: int, transaction_id: int, destination: int):
        #Write response tags
        self.write_tag(f'SORTER_{sorter_num}_RESPONSE.TRANSACTION_ID', transaction_id)
        self.write_tag(f'SORTER_{sorter_num}_RESPONSE.DESTINATION', destination)
        self.write_tag(f'SORTER_{sorter_num}_RESPONSE.END', 1)
        print(f"SORTER_{sorter_num}_RESPONSE: TRANS_ID: {transaction_id}, DEST: {destination}")

    def read_sorter_report(self, sorter_num: int):
        data = self.read_tag(f'SORTER_{sorter_num}_REPORT')
        if data is None:
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

            # Treat null/empty barcode as no report
            return None

    def send_watchdog_signal(self):
        self.write_tag('OPC_WATCHDOG', 1)
