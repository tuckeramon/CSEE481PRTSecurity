from Communication.Database import Database
from Communication.PRTDB import PRTDB
from PRTConfig import BARCODE_DESTINATION_MAP
def initialize_destinations(prtdb: PRTDB):
    for barcode, dest in zip(BARCODE_DESTINATION_MAP, BARCODE_DESTINATION_MAP.values()):
        prtdb.store_destination_info(barcode, dest)


def main():
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'ZXCLUSIV14e!',
        'database': 'prtdb'
    }
    prtdb = PRTDB(config)
    prtdb.get_destination_info()
   # prtdb.store_sorter_report(1, "0001", True, False, True, False)
    #prtdb.store_sorter_request(2, "0001", 1)
    #rtdb.store_sorter_response(1, 1, "0001", 2)


if __name__ == "__main__":
    main()


