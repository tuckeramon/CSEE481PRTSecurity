"""
Wazuh JSON Logger for PLC Security Events

This module demonstrates how industrial security events flow from
a PLC monitoring system to a SIEM (Security Information and Event Management)
platform like Wazuh.

DATA FLOW:
    PLC (Rockwell Logix)
        ↓ EtherNet/IP protocol
    PLCSecurityMonitor (reads PLC status)
        ↓ Python dict
    WazuhLogger (this module)
        ↓ JSON file
    Wazuh Agent (monitors file)
        ↓ Wazuh protocol
    Wazuh Server (correlates, alerts)

LOG FORMAT:
Each line is a complete JSON object (JSON Lines format).
This allows Wazuh to parse logs line-by-line without buffering.

Example log entry:
{
    "timestamp": "2024-01-15T10:30:45.123456",
    "source": "plc_security",
    "plc_ip": "192.168.1.51",
    "event_type": "MODE_CHANGE",
    "severity": "WARNING",
    "message": "Controller mode changed from Run to Program",
    ...
}
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class WazuhLogger:
    """
    Writes PLC security events to JSON log files for Wazuh ingestion.

    NOTES:
    - Uses JSON Lines format (one JSON object per line)
    - Implements log rotation to prevent files from growing too large
    - Includes all fields needed for SIEM correlation and alerting

    WAZUH INTEGRATION:
    The Wazuh agent monitors the log file and forwards events to the
    Wazuh server. The agent configuration specifies:
    - Log file location
    - JSON parsing rules
    - Which fields to extract
    """

    # Default log directory (relative to backend folder)
    DEFAULT_LOG_DIR = "logs/plc_security"

    # Maximum log file size before rotation (5 MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024

    # Number of rotated files to keep
    MAX_ROTATED_FILES = 10

    def __init__(self, log_dir: str = None, log_filename: str = "plc_security.json"):
        
        #Initialize the Wazuh logger.

        #param log_dir: Directory for log files (created if doesn't exist)
        #param log_filename: Name of the active log file
        
        # Determine log directory
        if log_dir is None:
            # Get the backend directory (parent of Communication folder)
            backend_dir = Path(__file__).parent.parent
            self.log_dir = backend_dir / self.DEFAULT_LOG_DIR
        else:
            self.log_dir = Path(log_dir)

        self.log_filename = log_filename
        self.log_path = self.log_dir / log_filename

        # Create log directory if it doesn't exist
        self._ensure_log_directory()

        print(f"WazuhLogger: Logging to {self.log_path}")

    def _ensure_log_directory(self):
        
        #Create the log directory if it doesn't exist.

        #NOTE: May want to require elevated positions to view these logs.

        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"WazuhLogger: Failed to create log directory: {e}")

    def _rotate_if_needed(self):
        
        #Rotate log file if it exceeds maximum size.
        #Rotation scheme: plc_security.json → plc_security.json.1 → .2 → etc.
        
        if not self.log_path.exists():
            return

        try:
            if self.log_path.stat().st_size >= self.MAX_FILE_SIZE:
                # Rotate existing files
                for i in range(self.MAX_ROTATED_FILES - 1, 0, -1):
                    old_path = self.log_dir / f"{self.log_filename}.{i}"
                    new_path = self.log_dir / f"{self.log_filename}.{i + 1}"
                    if old_path.exists():
                        old_path.rename(new_path)

                # Rotate current file to .1
                rotated_path = self.log_dir / f"{self.log_filename}.1"
                self.log_path.rename(rotated_path)

                print(f"WazuhLogger: Rotated log file to {rotated_path}")
        except Exception as e:
            print(f"WazuhLogger: Log rotation failed: {e}")

    def log_event(
        self,
        plc_ip: str,
        event_type: str,
        message: str,
        severity: str = "INFO",
        plc_name: str = None,
        plc_serial: str = None,
        event_code: str = None,
        previous_state: str = None,
        current_state: str = None,
        raw_data: Dict[str, Any] = None
    ) -> bool:
        """
        Write a security event to the JSON log file.

        :param plc_ip: IP address of the PLC
        :param event_type: Category (FAULT, MODE_CHANGE, CONNECTION, etc.)
        :param message: Human-readable description
        :param severity: INFO, WARNING, ERROR, or CRITICAL
        :param plc_name: Controller name from PLC
        :param plc_serial: Serial number for device verification
        :param event_code: Fault code or event identifier
        :param previous_state: Previous state (for change events)
        :param current_state: Current state
        :param raw_data: Additional data as dictionary

        :return: True if logged successfully, False otherwise
        """
        # Check if rotation is needed
        self._rotate_if_needed()

        # Build the log entry
        # This structure is designed for Wazuh parsing
        log_entry = {
            # Timestamp in ISO 8601 format (Wazuh standard)
            "timestamp": datetime.now().isoformat(),

            # Source identifier - used in Wazuh rules to match events
            "source": "plc_security",

            # PLC identification
            "plc_ip": plc_ip,
            "plc_name": plc_name,
            "plc_serial": plc_serial,

            # Event classification
            "event_type": event_type,
            "severity": severity,
            "event_code": event_code,

            # Event details
            "message": message,
            "previous_state": previous_state,
            "current_state": current_state,

            # Raw data for detailed analysis
            "raw_data": raw_data
        }

        # Remove None values to keep logs clean
        log_entry = {k: v for k, v in log_entry.items() if v is not None}

        try:
            # Write as JSON Lines (one JSON object per line)
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

            return True

        except Exception as e:
            print(f"WazuhLogger: Failed to write log: {e}")
            return False

    def get_log_path(self) -> str:
        
        #Return the path to the active log file.
        #This path is needed for Wazuh agent configuration.

        return str(self.log_path)

    def get_recent_logs(self, count: int = 100) -> list:
        
        #Read recent log entries from the file.

        #param count: Number of recent entries to return
        #returns List of log entry dictionaries
        
        if not self.log_path.exists():
            return []

        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Get last N lines and parse as JSON
            recent_lines = lines[-count:]
            logs = []
            for line in recent_lines:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

            return logs

        except Exception as e:
            print(f"WazuhLogger: Failed to read logs: {e}")
            return []


# =============================================================================
# EXAMPLE: How to use WazuhLogger
# =============================================================================
#
# from Communication.WazuhLogger import WazuhLogger
#
# # Initialize logger
# logger = WazuhLogger()
#
# # Log a mode change event
# logger.log_event(
#     plc_ip="192.168.1.51",
#     event_type="MODE_CHANGE",
#     message="Controller mode changed from Run to Program",
#     severity="WARNING",
#     plc_name="MainController",
#     previous_state="Run",
#     current_state="Program"
# )
#
# # Log a fault event
# logger.log_event(
#     plc_ip="192.168.1.51",
#     event_type="FAULT",
#     message="Major fault detected on PLC",
#     severity="CRITICAL",
#     event_code="0x0001",
#     raw_data={"fault_type": "major", "fault_code": 1}
# )
#
# # Check recent logs
# recent = logger.get_recent_logs(10)
# for log in recent:
#     print(f"{log['timestamp']} [{log['severity']}] {log['message']}")
# =============================================================================
