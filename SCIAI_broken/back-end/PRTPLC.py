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
            print(f"SORTER_REQUEST_{sorter_num}: END: 1, barcode: {data['BARCODE']}")
            #Clear tag
            self.write_tag(f'SORTER_{sorter_num}_REQUEST.END', 0)
            return data['BARCODE'], data['TRANSACTION_ID']

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
            print(f"Sorted_Report: {data}")
            return data['BARCODE'], data['FLAGS']['ACTIVE'], data['FLAGS']['LOST'], data['FLAGS']['GOOD'], data['FLAGS']['DIVERTED']
        
    def send_watchdog_signal(self):
        self.write_tag('OPC_WATCHDOG', 1)



