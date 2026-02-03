from flask import jsonify
import json

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

    # =========================================================================
    # PLC SECURITY LOGGING METHODS
    # For tracking security-relevant events from Rockwell Logix PLCs
    # =========================================================================

    # Severity levels for security events
    SEVERITY_INFO = "INFO"
    SEVERITY_WARNING = "WARNING"
    SEVERITY_ERROR = "ERROR"
    SEVERITY_CRITICAL = "CRITICAL"

    # Event types for categorization
    EVENT_FAULT = "FAULT"
    EVENT_MODE_CHANGE = "MODE_CHANGE"
    EVENT_CONNECTION = "CONNECTION"
    EVENT_STATUS = "STATUS"
    EVENT_CONFIG_CHANGE = "CONFIG_CHANGE"
    EVENT_BASELINE_DEVIATION = "BASELINE_DEVIATION"

    def log_plc_security_event(
        self,
        plc_ip: str,
        event_type: str,
        event_message: str,
        severity: str = "INFO",
        plc_name: str = None,
        plc_serial: str = None,
        event_code: str = None,
        previous_state: str = None,
        current_state: str = None,
        raw_data: dict = None,
        plc_timestamp: str = None
    ):
        """
        Log a security-relevant event from a PLC to the PLCSecurityLogs table.

        :param plc_ip: IP address of the PLC
        :param event_type: Category (FAULT, MODE_CHANGE, CONNECTION, STATUS, CONFIG_CHANGE)
        :param event_message: Human-readable description of the event
        :param severity: INFO, WARNING, ERROR, or CRITICAL
        :param plc_name: Controller name from PLC
        :param plc_serial: Serial number for device verification
        :param event_code: Fault code or event identifier
        :param previous_state: Previous state (for change events)
        :param current_state: Current state
        :param raw_data: Dictionary of raw PLC data (stored as JSON)
        :param plc_timestamp: Timestamp from PLC if available

        :return: Number of rows inserted (1 on success, 0 on failure)
        """
        query = """
        INSERT INTO PLCSecurityLogs
            (plc_ip, plc_name, plc_serial, event_type, severity, event_code,
             event_message, previous_state, current_state, raw_data, plc_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        raw_json = json.dumps(raw_data) if raw_data else None
        args = [(
            plc_ip, plc_name, plc_serial, event_type, severity, event_code,
            event_message, previous_state, current_state, raw_json, plc_timestamp
        )]
        try:
            result = self.insert(query, args)
            if severity in [self.SEVERITY_ERROR, self.SEVERITY_CRITICAL]:
                print(f"SECURITY [{severity}] {plc_ip}: {event_message}")
            return result
        except Exception as e:
            print(f"Error logging PLC security event: {e}")
            return 0

    def get_plc_baseline(self, plc_ip: str):
        """
        Get the expected baseline configuration for a PLC.
        Used to detect unauthorized changes.

        :param plc_ip: IP address of the PLC
        :return: Baseline dict or None if not found
        """
        query = """
        SELECT * FROM PLCBaseline WHERE plc_ip = %s
        """
        result = self.fetch(query, [plc_ip])
        if result:
            return result[0]
        return None

    def set_plc_baseline(
        self,
        plc_ip: str,
        plc_name: str = None,
        plc_serial: str = None,
        firmware_version: str = None,
        product_type: str = None,
        expected_mode: str = "Run"
    ):
        """
        Set or update the expected baseline configuration for a PLC.
        Call this after initial setup to establish the "known good" state.

        :param plc_ip: IP address of the PLC
        :param plc_name: Expected controller name
        :param plc_serial: Expected serial number
        :param firmware_version: Expected firmware version
        :param product_type: Expected product type
        :param expected_mode: Expected operating mode (Run, Program, Remote)

        :return: Number of rows affected
        """
        query = """
        INSERT INTO PLCBaseline
            (plc_ip, plc_name, plc_serial, firmware_version, product_type, expected_mode)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            plc_name = VALUES(plc_name),
            plc_serial = VALUES(plc_serial),
            firmware_version = VALUES(firmware_version),
            product_type = VALUES(product_type),
            expected_mode = VALUES(expected_mode),
            updated_at = CURRENT_TIMESTAMP
        """
        args = [(plc_ip, plc_name, plc_serial, firmware_version, product_type, expected_mode)]
        return self.insert(query, args)

    def get_recent_security_logs(self, plc_ip: str = None, limit: int = 100, severity: str = None):
        """
        Retrieve recent security logs, optionally filtered by PLC or severity.

        :param plc_ip: Filter by PLC IP (None for all PLCs)
        :param limit: Maximum number of logs to return
        :param severity: Filter by severity level (None for all)
        :return: List of log entries
        """
        query = "SELECT * FROM PLCSecurityLogs WHERE 1=1"
        args = []

        if plc_ip:
            query += " AND plc_ip = %s"
            args.append(plc_ip)

        if severity:
            query += " AND severity = %s"
            args.append(severity)

        query += " ORDER BY timestamp DESC LIMIT %s"
        args.append(limit)

        return self.fetch(query, args)

    def get_security_alerts(self, hours: int = 24):
        """
        Get security alerts (WARNING, ERROR, CRITICAL) from the last N hours.
        Useful for dashboard displays and alerting.

        :param hours: Number of hours to look back
        :return: List of alert entries
        """
        query = """
        SELECT * FROM PLCSecurityLogs
        WHERE severity IN ('WARNING', 'ERROR', 'CRITICAL')
        AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY timestamp DESC
        """
        return self.fetch(query, [hours])

    # =========================================================================
    # WAZUH ALERT STORAGE METHODS
    # For storing correlated/enriched alerts from the Wazuh SIEM manager.
    # These are DISTINCT from PLCSecurityLogs (raw events from PLCSecurityMonitor).
    # =========================================================================

    def store_wazuh_alert(
        self,
        wazuh_alert_id: str,
        wazuh_rule_id: str,
        wazuh_rule_level: int,
        wazuh_rule_description: str,
        wazuh_rule_groups: str = None,
        agent_id: str = None,
        agent_name: str = None,
        agent_ip: str = None,
        plc_ip: str = None,
        event_type: str = None,
        severity: str = None,
        event_message: str = None,
        previous_state: str = None,
        current_state: str = None,
        raw_alert: str = None,
        wazuh_timestamp=None
    ):
        """
        Store a Wazuh alert in the PLCSecurityAlerts table.

        Uses INSERT IGNORE to safely handle duplicate alert IDs
        (the wazuh_alert_id column has a UNIQUE index).

        :param wazuh_alert_id: Unique alert identifier (timestamp_ruleId_agentId)
        :param wazuh_rule_id: Wazuh rule ID that triggered (e.g., "100021")
        :param wazuh_rule_level: Wazuh severity level (0-15)
        :param wazuh_rule_description: Description from the rule definition
        :param wazuh_rule_groups: Comma-separated rule groups
        :param agent_id: Wazuh agent ID
        :param agent_name: Wazuh agent name
        :param agent_ip: Wazuh agent IP
        :param plc_ip: PLC IP from original event data
        :param event_type: Event type from original event
        :param severity: Severity from original event
        :param event_message: Message from original event
        :param previous_state: Previous state from original event
        :param current_state: Current state from original event
        :param raw_alert: Full Wazuh alert as JSON string
        :param wazuh_timestamp: Datetime when Wazuh generated the alert
        :return: Number of rows inserted (1 on success, 0 if duplicate)
        """
        query = """
        INSERT IGNORE INTO PLCSecurityAlerts
            (wazuh_alert_id, wazuh_rule_id, wazuh_rule_level, wazuh_rule_description,
             wazuh_rule_groups, agent_id, agent_name, agent_ip,
             plc_ip, event_type, severity, event_message,
             previous_state, current_state, raw_alert, wazuh_timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        args = [(
            wazuh_alert_id, wazuh_rule_id, wazuh_rule_level, wazuh_rule_description,
            wazuh_rule_groups, agent_id, agent_name, agent_ip,
            plc_ip, event_type, severity, event_message,
            previous_state, current_state, raw_alert, wazuh_timestamp
        )]
        try:
            return self.insert(query, args)
        except Exception as e:
            print(f"Error storing Wazuh alert: {e}")
            return 0

    def get_recent_wazuh_alerts(
        self,
        plc_ip: str = None,
        min_level: int = None,
        event_type: str = None,
        acknowledged: bool = None,
        limit: int = 100
    ):
        """
        Retrieve recent Wazuh alerts with optional filters.

        :param plc_ip: Filter by PLC IP address (None for all)
        :param min_level: Minimum Wazuh rule level 0-15 (None for all)
        :param event_type: Filter by event type (MODE_CHANGE, FAULT, etc.)
        :param acknowledged: Filter by acknowledgement status (True/False/None)
        :param limit: Maximum number of alerts to return
        :return: List of alert dictionaries
        """
        query = "SELECT * FROM PLCSecurityAlerts WHERE 1=1"
        args = []

        if plc_ip:
            query += " AND plc_ip = %s"
            args.append(plc_ip)

        if min_level is not None:
            query += " AND wazuh_rule_level >= %s"
            args.append(min_level)

        if event_type:
            query += " AND event_type = %s"
            args.append(event_type)

        if acknowledged is not None:
            query += " AND acknowledged = %s"
            args.append(1 if acknowledged else 0)

        query += " ORDER BY wazuh_timestamp DESC LIMIT %s"
        args.append(limit)

        return self.fetch(query, args)

    def acknowledge_alert(self, alert_id: int, acknowledged_by: str = None):
        """
        Mark a Wazuh alert as acknowledged by an operator.

        :param alert_id: The PLCSecurityAlerts.id of the alert to acknowledge
        :param acknowledged_by: Username or identifier of who acknowledged it
        :return: Number of rows updated (1 on success, 0 if not found)
        """
        query = """
        UPDATE PLCSecurityAlerts
        SET acknowledged = 1,
            acknowledged_by = %s,
            acknowledged_at = NOW()
        WHERE id = %s AND acknowledged = 0
        """
        args = (acknowledged_by, alert_id)
        return self.update(query, args)



