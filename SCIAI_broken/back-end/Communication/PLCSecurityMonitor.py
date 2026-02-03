"""
PLC Security Monitor for Rockwell Logix PLCs

EDUCATIONAL PURPOSE:
This module demonstrates industrial control system (ICS) security monitoring.
It connects to a Rockwell Automation Logix PLC and monitors for security-relevant
events that could indicate unauthorized access or system compromise.

DUAL OUTPUT LOGS:
Events are logged to two destinations:
1. MySQL Database (PLCSecurityLogs) - For frontend queries and historical analysis
2. JSON Log Files - For Wazuh SIEM ingestion and real-time alerting

This dual approach allows students to:
- Query the database directly to understand event structure
- Inspect raw JSON logs to see exactly what Wazuh receives
- Observe how the SIEM generates alerts

SECURITY EVENTS MONITORED:
- Controller faults (major/minor) - Hardware/software failures
- Mode changes (Run/Program/Remote) - Unauthorized access indicator
- Configuration changes (firmware, serial number) - Device tampering
- Connection anomalies - Network security issues
- Baseline deviations - Unauthorized modifications

Uses pycomm3 LogixDriver for EtherNet/IP communication with
Allen-Bradley CompactLogix and ControlLogix PLCs.
"""

from pycomm3 import LogixDriver
from typing import Optional, Dict, Any
import traceback

# Import the Wazuh JSON logger for dual output
from Communication.WazuhLogger import WazuhLogger


class PLCSecurityMonitor:
    """
    Security monitor for Rockwell Logix PLCs.

    Collects security-relevant data from PLCs and logs events
    to the database via PRTDB.
    """

    # Controller mode constants (from Rockwell documentation)
    MODE_PROGRAM = 0
    MODE_RUN = 1
    MODE_REMOTE = 2

    MODE_NAMES = {
        0: "Program",
        1: "Run",
        2: "Remote",
        # Some controllers may have additional modes
        6: "Run (Faulted)",
        7: "Program (Faulted)"
    }

    def __init__(self, plc_ip: str, prtdb, enable_wazuh: bool = True):
        """
        Initialize the security monitor for a specific PLC.
        This monitor implements dual-output logging:
        1. Database (prtdb) - For queries, frontend display, historical analysis
        2. Wazuh JSON (wazuh_logger) - For SIEM ingestion and real-time alerting

        :param plc_ip: IP address of the PLC to monitor
        :param prtdb: PRTDB instance for database operations
        :param enable_wazuh: Whether to enable Wazuh JSON logging (default: True)
        """
        self.plc_ip = plc_ip
        self.prtdb = prtdb
        self.driver: Optional[LogixDriver] = None

        # Initialize Wazuh JSON logger for SIEM integration
        # This creates a separate log file that Wazuh monitors
        self.enable_wazuh = enable_wazuh
        if enable_wazuh:
            self.wazuh_logger = WazuhLogger()
            print(f"PLCSecurityMonitor: Wazuh logging enabled -> {self.wazuh_logger.get_log_path()}")
        else:
            self.wazuh_logger = None

        # Cached state for change detection
        self._last_mode = None
        self._last_fault_count = 0
        self._last_info = None
        self._connected = False

    def _log_security_event(
        self,
        event_type: str,
        event_message: str,
        severity: str = "INFO",
        plc_name: str = None,
        plc_serial: str = None,
        event_code: str = None,
        previous_state: str = None,
        current_state: str = None,
        raw_data: Dict[str, Any] = None
    ):
        """
        DUAL OUTPUT: Log security event to BOTH database AND Wazuh JSON file.
        1. Database write - For persistence, queries, and frontend display
        2. JSON file write - For Wazuh SIEM ingestion

        - Wazuh can't parse MySQL data natively
        - JSON files are easy for Wazuh to monitor in real-time
        - Students can inspect both outputs to understand the data flow
        """
        # Output 1: Database (for frontend and historical queries)
        self.prtdb.log_plc_security_event(
            plc_ip=self.plc_ip,
            event_type=event_type,
            event_message=event_message,
            severity=severity,
            plc_name=plc_name,
            plc_serial=plc_serial,
            event_code=event_code,
            previous_state=previous_state,
            current_state=current_state,
            raw_data=raw_data
        )

        # Output 2: Wazuh JSON file (for SIEM ingestion)
        if self.wazuh_logger:
            self.wazuh_logger.log_event(
                plc_ip=self.plc_ip,
                event_type=event_type,
                message=event_message,
                severity=severity,
                plc_name=plc_name,
                plc_serial=plc_serial,
                event_code=event_code,
                previous_state=previous_state,
                current_state=current_state,
                raw_data=raw_data
            )

    def connect(self) -> bool:
        """
        Establish connection to the PLC.
        Logs connection events for security tracking.

        :return: True if connected successfully
        """
        try:
            self.driver = LogixDriver(self.plc_ip)
            self.driver.open()
            self._connected = True

            # Log successful connection (dual output: DB + Wazuh)
            self._log_security_event(
                event_type=self.prtdb.EVENT_CONNECTION,
                event_message=f"Security monitor connected to PLC at {self.plc_ip}",
                severity=self.prtdb.SEVERITY_INFO,
                current_state="Connected"
            )

            # Collect and verify initial state
            self._collect_initial_state()

            return True

        except Exception as e:
            self._connected = False
            self._log_security_event(
                event_type=self.prtdb.EVENT_CONNECTION,
                event_message=f"Failed to connect to PLC: {str(e)}",
                severity=self.prtdb.SEVERITY_ERROR,
                current_state="Disconnected",
                raw_data={"error": str(e)}
            )
            return False

    def disconnect(self):
        """Close connection to the PLC."""
        if self.driver:
            try:
                self.driver.close()
            except:
                pass
            self.driver = None
            self._connected = False

    def _collect_initial_state(self):
        """
        Collect initial PLC state and verify against baseline.
        Called after successful connection.
        """
        if not self._connected:
            return

        # Get PLC info
        info = self._get_plc_info()
        if info:
            self._last_info = info

            # Check against baseline
            baseline = self.prtdb.get_plc_baseline(self.plc_ip)

            if baseline:
                self._check_baseline_deviations(info, baseline)
            else:
                # No baseline exists - create one and log
                self._create_initial_baseline(info)

        # Get initial mode
        mode = self._get_controller_mode()
        if mode is not None:
            self._last_mode = mode

    def _get_plc_info(self) -> Optional[Dict[str, Any]]:
        """
        Get PLC identification and configuration info.

        :return: Dictionary with PLC info or None on failure
        """
        if not self.driver:
            return None

        try:
            # pycomm3 provides get_plc_info() method
            info = self.driver.get_plc_info()

            return {
                "product_type": info.get("product_type", "Unknown"),
                "product_name": info.get("product_name", "Unknown"),
                "serial_number": info.get("serial_number", "Unknown"),
                "revision": info.get("revision", "Unknown"),
                "vendor": info.get("vendor", "Rockwell Automation"),
                "name": self.driver.get_plc_name() if hasattr(self.driver, 'get_plc_name') else "Unknown"
            }
        except Exception as e:
            print(f"PLCSecurityMonitor: Error getting PLC info: {e}")
            return None

    def _get_controller_mode(self) -> Optional[int]:
        #Get the current controller operating mode.

        #returns Mode code (0=Program, 1=Run, 2=Remote) or None
        if not self.driver:
            return None

        try:
            # Try to read controller mode - tag name varies by PLC configuration
            # Common tag names for controller mode:
            mode_tags = [
                "Controller:Mode",      # Standard Logix tag
                "Mode",                 # Simplified
                "ControllerMode"        # Alternative
            ]

            for tag in mode_tags:
                try:
                    result = self.driver.read(tag)
                    if result and result.value is not None:
                        return int(result.value)
                except:
                    continue

            return None

        except Exception as e:
            print(f"PLCSecurityMonitor: Error reading controller mode: {e}")
            return None

    def _get_fault_info(self) -> Optional[Dict[str, Any]]:
        
        #Read fault information from the PLC.

        #returns Dictionary with fault data or None

        if not self.driver:
            return None

        try:
            faults = {
                "major_fault": False,
                "minor_fault": False,
                "fault_code": None,
                "fault_info": None
            }

            # Try to read fault tags - names vary by configuration
            fault_tags = [
                ("MajorFaultRecord", "major"),
                ("MinorFaultRecord", "minor"),
                ("Controller:MajorFault", "major"),
                ("Controller:MinorFault", "minor"),
                ("FaultCode", "code")
            ]

            for tag_name, fault_type in fault_tags:
                try:
                    result = self.driver.read(tag_name)
                    if result and result.value is not None:
                        if fault_type == "major":
                            faults["major_fault"] = bool(result.value)
                        elif fault_type == "minor":
                            faults["minor_fault"] = bool(result.value)
                        elif fault_type == "code":
                            faults["fault_code"] = result.value
                except:
                    continue

            return faults

        except Exception as e:
            print(f"PLCSecurityMonitor: Error reading faults: {e}")
            return None

    def _create_initial_baseline(self, info: Dict[str, Any]):
        #Create initial baseline from current PLC state.

        self.prtdb.set_plc_baseline(
            plc_ip=self.plc_ip,
            plc_name=info.get("name"),
            plc_serial=info.get("serial_number"),
            firmware_version=info.get("revision"),
            product_type=info.get("product_name"),
            expected_mode="Run"
        )

        self._log_security_event(
            event_type=self.prtdb.EVENT_STATUS,
            event_message=f"Initial baseline created for PLC: {info.get('product_name')} (SN: {info.get('serial_number')})",
            severity=self.prtdb.SEVERITY_INFO,
            plc_name=info.get("name"),
            plc_serial=info.get("serial_number"),
            raw_data=info
        )

    def _check_baseline_deviations(self, current: Dict[str, Any], baseline: Dict[str, Any]):
        
        #Compare current PLC state against baseline and log deviations.
        #Security-critical: detects unauthorized hardware/firmware changes.

        deviations = []

        # Check serial number (different device entirely!)
        if baseline.get("plc_serial") and current.get("serial_number"):
            if baseline["plc_serial"] != current["serial_number"]:
                deviations.append({
                    "field": "serial_number",
                    "expected": baseline["plc_serial"],
                    "actual": current["serial_number"],
                    "severity": self.prtdb.SEVERITY_CRITICAL,
                    "message": f"PLC SERIAL NUMBER CHANGED! Expected {baseline['plc_serial']}, found {current['serial_number']}. Possible device replacement."
                })

        # Check firmware version (could indicate unauthorized update)
        if baseline.get("firmware_version") and current.get("revision"):
            if baseline["firmware_version"] != current["revision"]:
                deviations.append({
                    "field": "firmware_version",
                    "expected": baseline["firmware_version"],
                    "actual": current["revision"],
                    "severity": self.prtdb.SEVERITY_WARNING,
                    "message": f"PLC firmware version changed from {baseline['firmware_version']} to {current['revision']}"
                })

        # Check product type (shouldn't change unless device replaced)
        if baseline.get("product_type") and current.get("product_name"):
            if baseline["product_type"] != current["product_name"]:
                deviations.append({
                    "field": "product_type",
                    "expected": baseline["product_type"],
                    "actual": current["product_name"],
                    "severity": self.prtdb.SEVERITY_CRITICAL,
                    "message": f"PLC product type changed! Expected {baseline['product_type']}, found {current['product_name']}"
                })

        # Log all deviations (dual output: DB + Wazuh)
        for dev in deviations:
            self._log_security_event(
                event_type=self.prtdb.EVENT_BASELINE_DEVIATION,
                event_message=dev["message"],
                severity=dev["severity"],
                plc_name=current.get("name"),
                plc_serial=current.get("serial_number"),
                previous_state=str(dev["expected"]),
                current_state=str(dev["actual"]),
                raw_data={"field": dev["field"], "baseline": baseline, "current": current}
            )

    def check_security_status(self) -> Dict[str, Any]:

        #Perform a security check of the PLC.
        #Call this periodically to detect security-relevant changes.

        #returns Dictionary with current security status

        status = {
            "connected": self._connected,
            "mode": None,
            "mode_name": "Unknown",
            "faults_detected": False,
            "events_logged": 0
        }

        if not self._connected:
            # Try to reconnect
            if not self.connect():
                return status

        events_logged = 0

        # Check controller mode
        current_mode = self._get_controller_mode()
        if current_mode is not None:
            status["mode"] = current_mode
            status["mode_name"] = self.MODE_NAMES.get(current_mode, f"Unknown ({current_mode})")

            # Detect mode changes
            if self._last_mode is not None and current_mode != self._last_mode:
                prev_name = self.MODE_NAMES.get(self._last_mode, f"Unknown ({self._last_mode})")
                curr_name = self.MODE_NAMES.get(current_mode, f"Unknown ({current_mode})")

                # Mode change is security-relevant - could indicate unauthorized access
                # EDUCATIONAL NOTE: Mode changes are a key ICS security indicator
                # Program mode allows code changes - this is especially concerning
                severity = self.prtdb.SEVERITY_WARNING
                if current_mode == self.MODE_PROGRAM:
                    # Going to Program mode is more concerning (allows code changes)
                    severity = self.prtdb.SEVERITY_ERROR

                self._log_security_event(
                    event_type=self.prtdb.EVENT_MODE_CHANGE,
                    event_message=f"Controller mode changed from {prev_name} to {curr_name}",
                    severity=severity,
                    previous_state=prev_name,
                    current_state=curr_name,
                    raw_data={"previous_mode": self._last_mode, "current_mode": current_mode}
                )
                events_logged += 1

            self._last_mode = current_mode

        # Check for faults
        fault_info = self._get_fault_info()
        if fault_info:
            if fault_info.get("major_fault"):
                status["faults_detected"] = True
                self._log_security_event(
                    event_type=self.prtdb.EVENT_FAULT,
                    event_message=f"MAJOR FAULT detected on PLC",
                    severity=self.prtdb.SEVERITY_CRITICAL,
                    event_code=str(fault_info.get("fault_code")),
                    current_state="Faulted",
                    raw_data=fault_info
                )
                events_logged += 1

            if fault_info.get("minor_fault"):
                status["faults_detected"] = True
                self._log_security_event(
                    event_type=self.prtdb.EVENT_FAULT,
                    event_message=f"Minor fault detected on PLC",
                    severity=self.prtdb.SEVERITY_WARNING,
                    event_code=str(fault_info.get("fault_code")),
                    current_state="Minor Fault",
                    raw_data=fault_info
                )
                events_logged += 1

        status["events_logged"] = events_logged
        return status

    def log_periodic_status(self):

        #Periodically log system status for auditing
        #Call this at regular intervals (e.g., every 5 minutes).

        if not self._connected:
            return

        info = self._get_plc_info()
        mode = self._get_controller_mode()
        fault_info = self._get_fault_info()

        self._log_security_event(
            event_type=self.prtdb.EVENT_STATUS,
            event_message=f"Periodic status: Mode={self.MODE_NAMES.get(mode, 'Unknown')}, Faults={'Yes' if fault_info and fault_info.get('major_fault') else 'No'}",
            severity=self.prtdb.SEVERITY_INFO,
            plc_name=info.get("name") if info else None,
            plc_serial=info.get("serial_number") if info else None,
            current_state=self.MODE_NAMES.get(mode, "Unknown"),
            raw_data={
                "info": info,
                "mode": mode,
                "faults": fault_info
            }
        )

    def read_custom_security_tags(self, tag_names: list) -> Dict[str, Any]:
        
        #Read custom security-related tags from the PLC.
        #Use this to monitor application-specific security indicators.
        #param tag_names: List of tag names to read
        #return: Dictionary of tag_name -> value
        
        results = {}

        if not self.driver:
            return results

        for tag in tag_names:
            try:
                result = self.driver.read(tag)
                if result:
                    results[tag] = result.value
            except Exception as e:
                results[tag] = f"Error: {e}"

        return results
