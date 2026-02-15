from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QDateTimeEdit, QPushButton, QHeaderView, QFrame,
    QSplitter, QMessageBox
)
from PyQt5.QtCore import QDateTime, Qt, QTimer, QThread, pyqtSignal
from PyQt5 import QtGui
from models.db import (
    fetch_security_logs, fetch_security_alerts, fetch_security_summary_stats,
    acknowledge_security_alert, fetch_distinct_plc_ips
)

SEVERITY_COLORS = {
    "CRITICAL": "#FFCDD2",
    "ERROR":    "#FFEBEE",
    "WARNING":  "#FFF3E0",
    "INFO":     "#E3F2FD",
}


class _DataLoadWorker(QThread):
    """Runs all security DB queries off the main thread."""
    finished = pyqtSignal(dict)

    def __init__(self, filters):
        super().__init__()
        self.filters = filters

    def run(self):
        severity, event_type, plc_ip, since_time = self.filters
        result = {
            "stats": fetch_security_summary_stats(),
            "alerts": fetch_security_alerts(
                severity=severity, event_type=event_type,
                plc_ip=plc_ip, since_time=since_time
            ),
            "logs": fetch_security_logs(
                severity=severity, event_type=event_type,
                plc_ip=plc_ip, since_time=since_time
            ),
        }
        self.finished.emit(result)


class SecurityLogView(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self._worker = None
        self._loading = False
        self.init_ui()
        self.setup_auto_refresh()

    def init_ui(self):
        self.setStyleSheet("background-color: #f2f2f2;")
        main_layout = QHBoxLayout()

        # Left side: main content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # 1) Stat cards row
        self.stat_cards_widget = self._build_stat_cards()
        content_layout.addWidget(self.stat_cards_widget)

        # 2) Splitter with two tables
        splitter = QSplitter(Qt.Vertical)

        alerts_container = self._build_alerts_table()
        splitter.addWidget(alerts_container)

        logs_container = self._build_logs_table()
        splitter.addWidget(logs_container)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        content_layout.addWidget(splitter)

        # Right side: filter panel
        filter_panel = self._build_filter_panel()

        main_layout.addWidget(content_widget, 4)
        main_layout.addWidget(filter_panel, 1)

        self.setLayout(main_layout)

    # -----------------------------------------------------------------
    # Build UI sections
    # -----------------------------------------------------------------

    def _build_stat_cards(self):
        container = QWidget()
        container.setFixedHeight(140)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        self.stat_labels = {}

        cards = [
            ("total_events_24h", "Events (24h)", "#002855", "#FFFFFF"),
            ("critical_count",   "CRITICAL",     "#D32F2F", "#FFFFFF"),
            ("error_count",      "ERROR",        "#C62828", "#FFFFFF"),
            ("warning_count",    "WARNING",      "#F57F17", "#FFFFFF"),
            ("unacknowledged_alerts", "Unack'd Alerts", "#EAAA00", "#002855"),
        ]

        for key, title, bg_color, text_color in cards:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {bg_color};
                    border-radius: 10px;
                    padding: 10px;
                }}
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setAlignment(Qt.AlignCenter)

            title_label = QLabel(title)
            title_label.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: bold; background: transparent; border: none;")
            title_label.setAlignment(Qt.AlignCenter)

            value_label = QLabel("0")
            value_label.setStyleSheet(f"color: {text_color}; font-size: 32px; font-weight: bold; background: transparent; border: none;")
            value_label.setAlignment(Qt.AlignCenter)

            card_layout.addWidget(title_label)
            card_layout.addWidget(value_label)

            self.stat_labels[key] = value_label
            layout.addWidget(card)

        return container

    def _build_alerts_table(self):
        container = QWidget()
        container.setStyleSheet("""
            background: #fff; border-radius: 12px;
            border: 1px solid #e0e0e0;
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 8, 12, 8)

        header_label = QLabel("Correlated Security Alerts")
        header_label.setStyleSheet("color: #002855; font-size: 16px; font-weight: bold; padding: 5px; background: transparent; border: none;")
        layout.addWidget(header_label)

        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(8)
        self.alerts_table.setHorizontalHeaderLabels([
            "Severity", "Rule ID", "Description", "PLC IP",
            "Event Count", "Detected At", "Status", "Action"
        ])
        self.alerts_table.horizontalHeader().setVisible(True)
        self.alerts_table.verticalHeader().setVisible(False)
        self.alerts_table.setAlternatingRowColors(False)
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.alerts_table.verticalHeader().setDefaultSectionSize(40)
        self.alerts_table.setFocusPolicy(Qt.NoFocus)
        self.alerts_table.setShowGrid(False)
        self.alerts_table.horizontalHeader().setHighlightSections(False)
        self.alerts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.alerts_table.setSelectionMode(QTableWidget.SingleSelection)
        self.alerts_table.setStyleSheet("""
            QTableWidget {
                background: #ffffff; border: none; font-size: 14px;
                color: #14213d; gridline-color: #e5e5e5;
            }
            QHeaderView::section {
                background-color: #002855; color: #fff;
                padding: 8px 0; font-size: 14px; font-weight: bold;
                border: none; border-bottom: 2px solid #ffc107;
            }
        """)

        # Description column stretches, others resize to content
        self.alerts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        for col in [0, 1, 3, 4, 5, 6, 7]:
            self.alerts_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)

        layout.addWidget(self.alerts_table)
        return container

    def _build_logs_table(self):
        container = QWidget()
        container.setStyleSheet("""
            background: #fff; border-radius: 12px;
            border: 1px solid #e0e0e0;
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 8, 12, 8)

        header_label = QLabel("Raw Security Events")
        header_label.setStyleSheet("color: #002855; font-size: 16px; font-weight: bold; padding: 5px; background: transparent; border: none;")
        layout.addWidget(header_label)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(7)
        self.logs_table.setHorizontalHeaderLabels([
            "Severity", "Event Type", "PLC IP", "Event Message",
            "Previous State", "Current State", "Timestamp"
        ])
        self.logs_table.horizontalHeader().setVisible(True)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.setAlternatingRowColors(False)
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.verticalHeader().setDefaultSectionSize(32)
        self.logs_table.setFocusPolicy(Qt.NoFocus)
        self.logs_table.setShowGrid(False)
        self.logs_table.horizontalHeader().setHighlightSections(False)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setSelectionMode(QTableWidget.SingleSelection)
        self.logs_table.setStyleSheet("""
            QTableWidget {
                background: #ffffff; border: none; font-size: 13px;
                color: #14213d; gridline-color: #e5e5e5;
            }
            QHeaderView::section {
                background-color: #002855; color: #fff;
                padding: 6px 0; font-size: 13px; font-weight: bold;
                border: none; border-bottom: 2px solid #ffc107;
            }
        """)

        # Event Message column stretches
        self.logs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        for col in [0, 1, 2, 4, 5, 6]:
            self.logs_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)

        layout.addWidget(self.logs_table)
        return container

    def _build_filter_panel(self):
        filter_panel = QWidget()
        filter_panel.setStyleSheet("""
            background-color: white; padding: 10px;
            border-radius: 8px; border: 1px solid #ddd;
        """)
        filter_layout = QVBoxLayout(filter_panel)

        title = QLabel("Filters")
        title.setStyleSheet("color: #002855; font-size: 18px; font-weight: bold;")
        filter_layout.addWidget(title)

        # Severity filter
        sev_label = QLabel("Severity:")
        sev_label.setStyleSheet("color: #002855; font-weight: bold;")
        filter_layout.addWidget(sev_label)
        self.severity_filter = QComboBox()
        self.severity_filter.setStyleSheet("color: #002855; font-weight: bold;")
        self.severity_filter.addItem("All", None)
        for sev in ["CRITICAL", "ERROR", "WARNING", "INFO"]:
            self.severity_filter.addItem(sev, sev)
        filter_layout.addWidget(self.severity_filter)

        # Event Type filter
        et_label = QLabel("Event Type:")
        et_label.setStyleSheet("color: #002855; font-weight: bold;")
        filter_layout.addWidget(et_label)
        self.event_type_filter = QComboBox()
        self.event_type_filter.setStyleSheet("color: #002855; font-weight: bold;")
        self.event_type_filter.addItem("All", None)
        for et in ["FAULT", "MODE_CHANGE", "CONNECTION", "STATUS",
                    "CONFIG_CHANGE", "BASELINE_DEVIATION", "FIREWALL_BLOCK", "FIREWALL_ALLOW"]:
            self.event_type_filter.addItem(et, et)
        filter_layout.addWidget(self.event_type_filter)

        # PLC IP filter (populated on first load, not during init)
        ip_label = QLabel("PLC IP:")
        ip_label.setStyleSheet("color: #002855; font-weight: bold;")
        filter_layout.addWidget(ip_label)
        self.plc_ip_filter = QComboBox()
        self.plc_ip_filter.setStyleSheet("color: #002855; font-weight: bold;")
        self.plc_ip_filter.addItem("All", None)
        filter_layout.addWidget(self.plc_ip_filter)
        self._plc_ips_loaded = False

        # Time range
        since_label = QLabel("Since:")
        since_label.setStyleSheet("color: #002855; font-weight: bold;")
        filter_layout.addWidget(since_label)
        self.time_filter = QDateTimeEdit()
        self.time_filter.setStyleSheet("color: #002855; font-weight: bold;")
        self.time_filter.setCalendarPopup(True)
        self.time_filter.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.time_filter.setDateTime(QDateTime.currentDateTime().addDays(-1))
        filter_layout.addWidget(self.time_filter)

        self.time_filter_dirty = False
        self.time_filter.dateTimeChanged.connect(self._on_time_filter_changed)

        # Buttons
        btn_style = """
            QPushButton {
                background-color: #002855; color: white;
                padding: 10px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #003a70; }
        """

        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setStyleSheet(btn_style)
        self.filter_btn.clicked.connect(self.load_all_data)
        filter_layout.addWidget(self.filter_btn)

        self.clear_btn = QPushButton("Clear Filters")
        self.clear_btn.setStyleSheet(btn_style)
        self.clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(self.clear_btn)

        self.refresh_btn = QPushButton("Refresh Now")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #EAAA00; color: #002855;
                padding: 10px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #ffc600; }
        """)
        self.refresh_btn.clicked.connect(self.load_all_data)
        filter_layout.addWidget(self.refresh_btn)

        filter_layout.addStretch()
        return filter_panel

    # -----------------------------------------------------------------
    # Data loading (background thread)
    # -----------------------------------------------------------------

    def _on_time_filter_changed(self):
        self.time_filter_dirty = True

    def _get_current_filters(self):
        severity = self.severity_filter.currentData()
        event_type = self.event_type_filter.currentData()
        plc_ip = self.plc_ip_filter.currentData()

        if self.time_filter_dirty:
            since_time = self.time_filter.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        else:
            since_time = None

        return severity, event_type, plc_ip, since_time

    def load_all_data(self):
        """Kick off a background thread to fetch all data."""
        if self._loading:
            return  # Skip if a load is already in progress

        self._loading = True
        filters = self._get_current_filters()
        self._worker = _DataLoadWorker(filters)
        self._worker.finished.connect(self._on_data_loaded)
        self._worker.start()

    def _on_data_loaded(self, result):
        """Called on main thread when the worker finishes."""
        self._loading = False

        # Populate PLC IP dropdown on first successful load
        if not self._plc_ips_loaded:
            self._plc_ips_loaded = True
            ips = fetch_distinct_plc_ips()
            for ip in ips:
                self.plc_ip_filter.addItem(ip, ip)

        # Update stat cards
        stats = result.get("stats", {})
        for key, label in self.stat_labels.items():
            label.setText(str(stats.get(key, 0)))

        # Update alerts table
        self._populate_alerts_table(result.get("alerts", []))

        # Update logs table
        self._populate_logs_table(result.get("logs", []))

    def _populate_alerts_table(self, alerts):
        self.alerts_table.setRowCount(len(alerts))
        for i, alert in enumerate(alerts):
            sev = alert.get("severity", "")
            row_color = QtGui.QColor(SEVERITY_COLORS.get(sev, "#FFFFFF"))

            detected = alert.get("detected_at")
            detected_str = detected.strftime("%Y-%m-%d %H:%M:%S") if hasattr(detected, "strftime") else str(detected or "")

            is_acked = alert.get("acknowledged", 0) == 1
            status_text = "Acknowledged" if is_acked else "UNACKNOWLEDGED"

            values = [
                sev,
                alert.get("rule_id", ""),
                alert.get("rule_description", ""),
                alert.get("plc_ip", ""),
                str(alert.get("matched_event_count", "")),
                detected_str,
                status_text,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                font = item.font()
                font.setPointSize(12)
                if col == 0:
                    font.setBold(True)
                item.setFont(font)
                item.setBackground(row_color)
                item.setForeground(QtGui.QBrush(QtGui.QColor("#14213d")))
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.alerts_table.setItem(i, col, item)

            # Action column: acknowledge button or ack info
            if not is_acked:
                ack_btn = QPushButton("Acknowledge")
                ack_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #EAAA00; color: #002855;
                        padding: 4px 8px; border-radius: 3px; font-weight: bold; font-size: 12px;
                    }
                    QPushButton:hover { background-color: #ffc600; }
                """)
                alert_db_id = alert.get("id")
                ack_btn.clicked.connect(lambda checked, aid=alert_db_id: self._acknowledge_alert(aid))
                self.alerts_table.setCellWidget(i, 7, ack_btn)
            else:
                ack_by = alert.get("acknowledged_by", "") or ""
                ack_at = alert.get("acknowledged_at")
                ack_at_str = ack_at.strftime("%m/%d %H:%M") if hasattr(ack_at, "strftime") else str(ack_at or "")
                ack_item = QTableWidgetItem(f"{ack_by} @ {ack_at_str}")
                ack_font = ack_item.font()
                ack_font.setPointSize(11)
                ack_item.setFont(ack_font)
                ack_item.setBackground(row_color)
                ack_item.setForeground(QtGui.QBrush(QtGui.QColor("#666666")))
                ack_item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.alerts_table.setItem(i, 7, ack_item)

    def _acknowledge_alert(self, alert_id):
        username = self.user.get("username", "unknown")
        reply = QMessageBox.question(
            self, "Confirm Acknowledge",
            f"Mark alert #{alert_id} as acknowledged by {username}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success = acknowledge_security_alert(alert_id, username)
            if success:
                self.load_all_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to acknowledge alert. It may already be acknowledged.")

    def _populate_logs_table(self, logs):
        self.logs_table.setRowCount(len(logs))
        for i, log in enumerate(logs):
            sev = log.get("severity", "")
            row_color = QtGui.QColor(SEVERITY_COLORS.get(sev, "#FFFFFF"))

            ts = log.get("timestamp")
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts or "")

            values = [
                sev,
                log.get("event_type", ""),
                log.get("plc_ip", ""),
                log.get("event_message", ""),
                log.get("previous_state", "") or "",
                log.get("current_state", "") or "",
                ts_str,
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                font = item.font()
                font.setPointSize(11)
                if col == 0:
                    font.setBold(True)
                item.setFont(font)
                item.setBackground(row_color)
                item.setForeground(QtGui.QBrush(QtGui.QColor("#14213d")))
                if col == 3:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                else:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.logs_table.setItem(i, col, item)

    # -----------------------------------------------------------------
    # Filter reset
    # -----------------------------------------------------------------

    def clear_filters(self):
        self.severity_filter.setCurrentIndex(0)
        self.event_type_filter.setCurrentIndex(0)
        self.plc_ip_filter.setCurrentIndex(0)
        self.time_filter.blockSignals(True)
        self.time_filter.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.time_filter.blockSignals(False)
        self.time_filter_dirty = False
        self.load_all_data()

    # -----------------------------------------------------------------
    # Auto-refresh
    # -----------------------------------------------------------------

    def setup_auto_refresh(self):
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.load_all_data)
        self.refresh_timer.setInterval(10000)

    def showEvent(self, event):
        super().showEvent(event)
        self.load_all_data()
        self.refresh_timer.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.refresh_timer.stop()
