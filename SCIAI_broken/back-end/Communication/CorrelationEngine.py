"""
SQL-Based Correlation Engine for PLC Security

Queries the PLCSecurityLogs table for attack patterns and stores
correlated alerts in the PLCSecurityAlerts table.

CORRELATION RULES:
    CORR_001 - Rapid Mode Changes:
        3+ MODE_CHANGE events within 300 seconds on the same PLC.
        Indicates possible unauthorized access or attack.

    CORR_002 - Connection Brute Force:
        5+ CONNECTION errors within 60 seconds on the same PLC.
        Indicates possible brute force or network attack.

    CORR_003 - Fault After Mode Change:
        A CRITICAL FAULT occurring within 300 seconds after a MODE_CHANGE
        on the same PLC. Indicates possible malicious code execution.

    CORR_004 - Firewall Scan Detection:
        10+ FIREWALL_BLOCK events from the same source IP within 120 seconds.
        Indicates a port scan or persistent unauthorized access attempt.

DATA FLOW:
    PLCSecurityMonitor writes events to PLCSecurityLogs (MySQL)
        |
    CorrelationEngine.run_correlation() (called every 10s from main loop)
        | queries PLCSecurityLogs for patterns
    PRTDB.store_correlation_alert() -> PLCSecurityAlerts table
"""

from time import time


class CorrelationEngine:
    """
    SQL-based correlation engine that detects attack patterns
    by querying PLCSecurityLogs and storing alerts in PLCSecurityAlerts.

    Designed to be called periodically from the main polling loop,
    similar to how PLCSecurityMonitor.check_security_status() is called.
    """

    def __init__(self, prtdb):
        """
        Initialize the correlation engine.

        :param prtdb: PRTDB instance for database operations
        """
        self.prtdb = prtdb

        # Statistics
        self._alerts_generated = 0
        self._checks_performed = 0

    def run_correlation(self) -> int:
        """
        Run all correlation rules and return the number of new alerts generated.
        Called periodically from main.py's polling loop.

        :return: Total number of new alerts generated across all rules
        """
        count = 0

        try:
            count += self._check_rapid_mode_changes()
            count += self._check_connection_brute_force()
            count += self._check_fault_after_mode_change()
            count += self._check_firewall_scan()
        except Exception as e:
            print(f"CorrelationEngine: Error during correlation: {e}")

        self._checks_performed += 1

        if count > 0:
            self._alerts_generated += count
            print(f"CorrelationEngine: Generated {count} new alert(s)")

        return count

    def _generate_alert_id(self, rule_id: str, plc_ip: str, time_bucket: int) -> str:
        """
        Generate a deterministic alert ID for deduplication.

        The time_bucket groups alerts into windows so the same pattern
        doesn't generate duplicate alerts within the same time period.

        :param rule_id: Correlation rule ID (e.g., "CORR_001")
        :param plc_ip: PLC IP address
        :param time_bucket: Unix timestamp rounded to the rule's timeframe
        :return: Unique alert identifier string
        """
        return f"{rule_id}_{plc_ip}_{time_bucket}"

    def _get_time_bucket(self, timeframe_seconds: int) -> int:
        """
        Get the current time bucket for deduplication.
        Rounds current time down to the nearest timeframe interval.

        :param timeframe_seconds: Size of the time bucket in seconds
        :return: Unix timestamp of the current bucket start
        """
        now = int(time())
        return now - (now % timeframe_seconds)

    def _check_rapid_mode_changes(self) -> int:
        """
        CORR_001: Detect 3+ mode changes within 300 seconds on the same PLC.

        :return: Number of new alerts generated
        """
        timeframe = 300  # 5 minutes
        threshold = 3

        results = self.prtdb.count_events_in_window(
            event_type="MODE_CHANGE",
            severity=None,
            timeframe_seconds=timeframe
        )

        count = 0
        time_bucket = self._get_time_bucket(timeframe)

        for row in results:
            if row["event_count"] >= threshold:
                alert_id = self._generate_alert_id("CORR_001", row["plc_ip"], time_bucket)

                stored = self.prtdb.store_correlation_alert(
                    alert_id=alert_id,
                    rule_id="CORR_001",
                    rule_level=14,
                    rule_description="Multiple mode changes detected - possible attack",
                    plc_ip=row["plc_ip"],
                    event_type="MODE_CHANGE",
                    severity="CRITICAL",
                    event_message=f"{row['event_count']} mode changes on {row['plc_ip']} in {timeframe}s",
                    matched_event_count=row["event_count"],
                    time_window_seconds=timeframe,
                    matched_log_ids=row.get("log_ids")
                )
                if stored > 0:
                    count += 1

        return count

    def _check_connection_brute_force(self) -> int:
        """
        CORR_002: Detect 5+ connection failures within 60 seconds on the same PLC.

        :return: Number of new alerts generated
        """
        timeframe = 60  # 1 minute
        threshold = 5

        results = self.prtdb.count_events_in_window(
            event_type="CONNECTION",
            severity="ERROR",
            timeframe_seconds=timeframe
        )

        count = 0
        time_bucket = self._get_time_bucket(timeframe)

        for row in results:
            if row["event_count"] >= threshold:
                alert_id = self._generate_alert_id("CORR_002", row["plc_ip"], time_bucket)

                stored = self.prtdb.store_correlation_alert(
                    alert_id=alert_id,
                    rule_id="CORR_002",
                    rule_level=12,
                    rule_description="Multiple connection failures detected - possible attack",
                    plc_ip=row["plc_ip"],
                    event_type="CONNECTION",
                    severity="CRITICAL",
                    event_message=f"{row['event_count']} connection failures to {row['plc_ip']} in {timeframe}s",
                    matched_event_count=row["event_count"],
                    time_window_seconds=timeframe,
                    matched_log_ids=row.get("log_ids")
                )
                if stored > 0:
                    count += 1

        return count

    def _check_fault_after_mode_change(self) -> int:
        """
        CORR_003: Detect a critical fault occurring within 300 seconds
        after a mode change on the same PLC.

        :return: Number of new alerts generated
        """
        timeframe = 300  # 5 minutes

        results = self.prtdb.find_faults_after_mode_changes(
            fault_window_seconds=timeframe
        )

        count = 0
        time_bucket = self._get_time_bucket(timeframe)

        for row in results:
            alert_id = self._generate_alert_id("CORR_003", row["plc_ip"], time_bucket)

            stored = self.prtdb.store_correlation_alert(
                alert_id=alert_id,
                rule_id="CORR_003",
                rule_level=13,
                rule_description="Fault after mode change - possible malicious code execution",
                plc_ip=row["plc_ip"],
                event_type="FAULT",
                severity="CRITICAL",
                event_message=f"Critical fault on {row['plc_ip']} after recent mode change",
                matched_event_count=2,
                time_window_seconds=timeframe,
                matched_log_ids=row.get("log_ids")
            )
            if stored > 0:
                count += 1

        return count

    def _check_firewall_scan(self) -> int:
        """
        CORR_004: Detect 10+ firewall blocks from the same IP within 120 seconds.
        Indicates a port scan or persistent unauthorized access attempt.

        :return: Number of new alerts generated
        """
        timeframe = 120  # 2 minutes
        threshold = 10

        results = self.prtdb.count_firewall_blocks_in_window(
            timeframe_seconds=timeframe
        )

        count = 0
        time_bucket = self._get_time_bucket(timeframe)

        for row in results:
            if row["event_count"] >= threshold:
                alert_id = self._generate_alert_id("CORR_004", row["plc_ip"], time_bucket)

                stored = self.prtdb.store_correlation_alert(
                    alert_id=alert_id,
                    rule_id="CORR_004",
                    rule_level=15,
                    rule_description="Persistent unauthorized access attempts detected - possible attack",
                    plc_ip=row["plc_ip"],
                    event_type="FIREWALL_BLOCK",
                    severity="CRITICAL",
                    event_message=f"{row['event_count']} blocked connection attempts from {row['plc_ip']} in {timeframe}s",
                    matched_event_count=row["event_count"],
                    time_window_seconds=timeframe,
                    matched_log_ids=row.get("log_ids")
                )
                if stored > 0:
                    count += 1

        return count

    def get_stats(self) -> dict:
        """
        Return correlation engine statistics.

        :return: Dictionary with engine stats
        """
        return {
            "alerts_generated": self._alerts_generated,
            "checks_performed": self._checks_performed
        }
