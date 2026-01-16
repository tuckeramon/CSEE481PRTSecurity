from flask import jsonify

from Communication.Database import Database


class PRTDB(Database):
    def store_sorter_request(self, sorter: int, barcode: str, transaction_id: int):
        """
        Insert a sorter request record into the database.
        """
        query = """
        INSERT INTO PRTSorterRequest (sorterID, transactionID, barcode)
        VALUES (%s, %s, %s)
        """
        args = [(sorter, transaction_id, str(barcode).zfill(4))]
        return self.insert(query, args)

    def store_sorter_response(self, sorter: int, transaction_id: int, barcode: str, destination: int):
        """
        Insert a sorter response record into the database.
        """
        query = """
        INSERT INTO PRTSorterResponse (sorterID, barcode, transactionID, destination)
        VALUES (%s, %s, %s, %s)
        """
        args = [(sorter, barcode, transaction_id, destination)]
        return self.insert(query, args)

    def store_sorter_report(self, sorter: int, barcode: str, active: bool, lost: bool, good: bool, diverted: bool):
        """
        Insert a sorter report record into the database.
        """
        query = """
        INSERT INTO PRTSorterReport (sorterID, barcode, active, lost, good, diverted)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        args = [(sorter, barcode, int(active), int(lost), int(good), int(diverted))]
        return self.insert(query, args)

    def store_destination_info(self, barcode: str, destination: int):
        """
        Insert a record containing the destination for a barcode into the database.
        """
        query = """
        INSERT INTO PRTCarts (barcode, destination)
        VALUES (%s, %s)
        """
        args = [(barcode, destination)]
        return self.insert(query, args)
    
    def update_destination_info(self, barcode: str, destination: int):
        """
        Update the destination for a specific barcode in the database.
        """
        query = """
        UPDATE PRTCarts
        SET destination = %s
        WHERE barcode = %s
        """
        args = (destination, barcode)
        return self.update(query, args)

    def get_destination_info(self, barcode: str):
        """
        Get a destination associated with a specific barcode from the database.
        """
        query = """
        SELECT * FROM PRTCarts
        WHERE BARCODE = %s
        """
        args = [(barcode)]
        result = self.fetch(query, args)
        if not result:
            return None
        return result[0]
    
    def get_destinations_info(self):
        """
        Get all destination records for valid barcodes from the database.
        """
        query = """
        SELECT * FROM PRTCarts
        """
        args = []
        return self.fetch(query, args)
    
    def store_remove_cart(self, barcode: str, area: int):
        """
        Insert a record containing the removal request of a cart into the database.
        """
        query = """
        INSERT INTO PRTRemoveCart (barcode, area)
        VALUES (%s, %s)
        """
        args = [(barcode, area)]
        return self.insert(query, args)



