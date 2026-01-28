from flask import jsonify

from Communication.Database import Database


class PRTDB(Database):
    """
    PRT Database access layer for PLC communication and activity logging

    MAJOR CHANGE: Now writes to BOTH PRT tables AND cart_logs table
    Old behavior: Only wrote to PRTSorterRequest/Response/Report tables
    New behavior: ALSO writes human-readable activity logs to cart_logs table for GUI

    This eliminates the need for HTTP-based logging (removed log_server.py)
    """

    # NEW: Position mappings for cart_logs table
    # Maps sorter numbers and destinations to frontend-compatible position strings
    # These match the ALLOWED_POSITIONS enum in front-end/models/db.py
    SORTER_TO_POSITION = {
        1: "Segment_A",  # Sorter 1 location (when cart is being scanned/sorted)
        2: "Segment_B"   # Sorter 2 location (when cart is being scanned/sorted)
    }

    DESTINATION_TO_POSITION = {
        1: "Station_1",  # Physical destination station 1
        2: "Station_2",  # Physical destination station 2
        3: "Station_3",  # Physical destination station 3
        4: "Station_4"   # Physical destination station 4
    }

    def _map_report_status(self, active: bool, lost: bool, good: bool, diverted: bool) -> str:
        """
        NEW METHOD: Convert PLC report status flags to human-readable event string

        PLC sends boolean flags (active, lost, good, diverted) in sorter reports
        This converts them to readable status strings for the frontend activity log

        Maps to EVENT_MAP from front-end/models/db.py:
        - "0010" → "Lost"
        - "0101" → "Good & Diverted"
        - "0100" → "Diverted"
        - "0000" → "Not Diverted"

        Returns human-readable status for cart_logs.event column
        """
        if lost:
            return "Lost"  # Cart was lost during processing (error condition)
        elif good and diverted:
            return "Good & Diverted"  # Cart successfully diverted to correct destination
        elif diverted:
            return "Diverted"  # Cart diverted (but not marked as "good")
        elif active:
            return "Active"  # Cart is actively being processed
        else:
            return "Not Diverted"  # Cart passed through without diversion

    def log_to_cart_logs(self, cart_id: str, position: str, event: str, action_type: str = None):
        """
        NEW METHOD: Write activity log entry directly to cart_logs table via SQL

        OLD BEHAVIOR: Would have sent HTTP POST to log_server.py (port 5000) which then
                      wrote to cart_logs. But HTTP layer was never actually connected!

        NEW BEHAVIOR: Direct SQL INSERT to cart_logs table in same database transaction
                      Eliminates HTTP overhead, simplifies architecture, ensures logging works

        This method is called automatically by:
        - store_sorter_request() - logs when cart enters sorter
        - store_sorter_response() - logs when routing decision is made
        - store_sorter_report() - logs final cart status (lost/diverted/etc)

        :param cart_id: Cart/barcode identifier (e.g., "0001")
        :param position: Position/location (Station_1-4, Segment_A-F) - from mapping constants
        :param event: Event description (Request, Response, Lost, Diverted, etc.)
        :param action_type: Action type (Request, Response, Report) - matches PLC operation type

        Returns: Number of rows inserted (1 on success, 0 on failure)
        """
        query = """
        INSERT INTO cart_logs (cart_id, position, event, action_type)
        VALUES (%s, %s, %s, %s)
        """
        args = [(cart_id, position, event, action_type)]
        try:
            return self.insert(query, args)
        except Exception as e:
            # IMPORTANT: Log error but don't fail the main operation
            # If cart_logs write fails, we still want PRT tables to be updated
            # Activity logging is non-critical compared to PLC communication
            print(f"Warning: Failed to log to cart_logs: {e}")
            return 0

    def store_sorter_request(self, sorter: int, barcode: str, transaction_id: int):
        """
        Insert a sorter request record into the database

        Called when PLC detects a cart and requests routing information

        CHANGE: Now writes to TWO tables instead of one:
        1. PRTSorterRequest - Technical PLC data (sorterID, transactionID, barcode)
        2. cart_logs - Human-readable activity log (cart at Segment_A, event: Request)

        OLD: Only wrote to PRTSorterRequest
        NEW: Also calls log_to_cart_logs() for frontend activity tracking
        """
        query = """
        INSERT INTO PRTSorterRequest (sorterID, transactionID, barcode)
        VALUES (%s, %s, %s)
        """
        args = [(sorter, transaction_id, str(barcode).zfill(4))]
        result = self.insert(query, args)

        # NEW: Also log to cart_logs for frontend activity tracking
        # Maps sorter number to position name (1 → "Segment_A", 2 → "Segment_B")
        position = self.SORTER_TO_POSITION.get(sorter, f"Sorter_{sorter}")
        self.log_to_cart_logs(
            cart_id=str(barcode).zfill(4),
            position=position,
            event="Request",
            action_type="Request"
        )

        return result

    def store_sorter_response(self, sorter: int, transaction_id: int, barcode: str, destination: int):
        """
        Insert a sorter response record into the database

        Called when system sends routing instructions back to PLC

        CHANGE: Now writes to TWO tables instead of one:
        1. PRTSorterResponse - Technical PLC data (which sorter, transaction ID, destination code)
        2. cart_logs - Human-readable activity log (cart routed to Station_1, event: Response)

        OLD: Only wrote to PRTSorterResponse
        NEW: Also calls log_to_cart_logs() with destination station name
        """
        query = """
        INSERT INTO PRTSorterResponse (sorterID, barcode, transactionID, destination)
        VALUES (%s, %s, %s, %s)
        """
        args = [(sorter, barcode, transaction_id, destination)]
        result = self.insert(query, args)

        # NEW: Also log to cart_logs with destination position
        # Maps destination number to station name (1 → "Station_1", 2 → "Station_2", etc.)
        position = self.DESTINATION_TO_POSITION.get(destination, f"Destination_{destination}")
        self.log_to_cart_logs(
            cart_id=str(barcode).zfill(4),
            position=position,
            event="Response",
            action_type="Response"
        )

        return result

    def store_sorter_report(self, sorter: int, barcode: str, active: bool, lost: bool, good: bool, diverted: bool):
        """
        Insert a sorter report record into the database

        Called when PLC reports final status of cart processing

        CHANGE: Now writes to TWO tables instead of one:
        1. PRTSorterReport - Technical PLC data (boolean flags: active, lost, good, diverted)
        2. cart_logs - Human-readable activity log (cart at Segment_A, event: "Lost" or "Good & Diverted")

        OLD: Only wrote raw boolean flags to PRTSorterReport
        NEW: Also converts flags to readable status and logs to cart_logs
             Uses _map_report_status() helper to convert flags to strings like "Lost", "Diverted", etc.
        """
        query = """
        INSERT INTO PRTSorterReport (sorterID, barcode, active, lost, good, diverted)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        args = [(sorter, barcode, int(active), int(lost), int(good), int(diverted))]
        result = self.insert(query, args)

        # NEW: Also log to cart_logs with human-readable status
        position = self.SORTER_TO_POSITION.get(sorter, f"Sorter_{sorter}")
        event = self._map_report_status(active, lost, good, diverted)  # Convert flags to "Lost", "Diverted", etc.
        self.log_to_cart_logs(
            cart_id=str(barcode).zfill(4),
            position=position,
            event=event,  # Human-readable status instead of raw flags
            action_type="Report"
        )

        return result

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

    def fetch_pending_removal_commands(self):
        """
        Fetch all pending cart removal commands from PRTRemoveCart.
        Called by main.py to poll for new removal requests from frontend.

        Returns: List of dicts with 'id', 'barcode', 'area', 'timestamp'
        """
        query = """
        SELECT id, barcode, area, timestamp
        FROM PRTRemoveCart
        ORDER BY timestamp ASC
        """
        return self.fetch(query, [])

    def delete_removal_command(self, command_id: int):
        """
        Delete a removal command after it has been processed.
        Called after successfully sending removal command to PLC.

        :param command_id: The id of the PRTRemoveCart record to delete
        """
        query = """
        DELETE FROM PRTRemoveCart
        WHERE id = %s
        """
        return self.update(query, (command_id,))

    def process_removal_command(self, command_id: int, barcode: str, area: int):
        """
        Process a removal command: log it and delete from pending.
        Called by main.py after PLC acknowledges removal.

        :param command_id: PRTRemoveCart.id
        :param barcode: Cart barcode
        :param area: Removal area
        """
        # Log to cart_logs for activity tracking
        self.log_to_cart_logs(
            cart_id=str(barcode).zfill(4),
            position=f"Area_{area}",
            event="Removed",
            action_type="Removal"
        )

        # Delete the processed command
        self.delete_removal_command(command_id)
        print(f"Processed removal: cart {barcode} to area {area}")



