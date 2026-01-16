from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QDateTimeEdit, QPushButton, QHeaderView
)
from PyQt5.QtCore import QDateTime, Qt
from PyQt5 import QtGui
from models.db import fetch_filtered_logs, fetch_all_cart_ids

class ActivityLogView(QWidget):
    def __init__(self, db_conn):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #f2f2f2;")
        main_layout = QHBoxLayout()

        # Table container with card style
        table_container = QWidget()
        table_container.setStyleSheet("""
            background: #fff;
            border-radius: 12px;
            padding: 12px;
            border: 1px solid #e0e0e0;
        """)
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Cart ID", "Position", "Event Type", "Event", "Time"])
        self.table.horizontalHeader().setVisible(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.horizontalHeader().setHighlightSections(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)

        # Style the main table and the header
        self.table.setStyleSheet("""
            QTableWidget {
                background: #ffffff;
                border: none;
                font-size: 15px;
                color: #14213d;
                alternate-background-color: #f7fafd;
                selection-background-color: #e9c46a;
                selection-color: #14213d;
                gridline-color: #e5e5e5;
            }
            QHeaderView::section {
                background-color: #002855;
                color: #fff;
                padding: 10px 0;
                font-size: 18px;
                font-weight: bold;
                border: none;
                border-bottom: 2px solid #ffc107;
            }
        """)

        # Set header font/bold
        header = self.table.horizontalHeader()
        font = header.font()
        font.setBold(True)
        font.setPointSize(30)
        header.setFont(font)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignVCenter | Qt.AlignCenter)

        table_layout.addWidget(self.table)

        # Sidebar: Filter panel on the right
        filter_panel = QWidget()
        filter_panel.setStyleSheet("""
            background-color: white;
            padding: 10px;
            border-radius: 8px;
            border: 1px solid #ddd;
        """)
        filter_layout = QVBoxLayout(filter_panel)

        # Cart filter
        cart_label = QLabel("Cart ID:")
        cart_label.setStyleSheet("color: #002855; font-weight: bold;")
        filter_layout.addWidget(cart_label)
        self.cart_filter = QComboBox()
        self.cart_filter.setStyleSheet("color: #002855; font-weight: bold;")
        self.cart_filter.addItem("All", None)
        for cart_id in fetch_all_cart_ids():
            self.cart_filter.addItem(cart_id, cart_id)
        filter_layout.addWidget(self.cart_filter)

        # Station filter
        station_label = QLabel("Station:")
        station_label.setStyleSheet("color: #002855; font-weight: bold;")
        filter_layout.addWidget(station_label)
        self.station_filter = QComboBox()
        self.station_filter.setStyleSheet("color: #002855; font-weight: bold;")
        self.station_filter.addItem("All", None)
        for station in [
            "Station_1", "Station_2", "Station_3", "Station_4",
            "Segment_A", "Segment_B"
        ]:
            self.station_filter.addItem(station, station)
        filter_layout.addWidget(self.station_filter)

        # Time filter
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
        self.filter_btn = QPushButton("Filter")
        self.filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #002855;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #003a70;
            }
        """)
        self.filter_btn.clicked.connect(self.load_logs)
        filter_layout.addWidget(self.filter_btn)

        self.clear_btn = QPushButton("Clear Filters")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #002855;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #003a70;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(self.clear_btn)

        filter_layout.addStretch()

        # Add to main layout
        main_layout.addWidget(table_container, 3)
        main_layout.addWidget(filter_panel, 1)

        self.setLayout(main_layout)
        self.load_logs()

    def _on_time_filter_changed(self):
        self.time_filter_dirty = True

    def load_logs(self):
        cart_id = self.cart_filter.currentData()
        position = self.station_filter.currentData()

        if self.time_filter_dirty:
            selected_time = self.time_filter.dateTime()
            time_stamp = selected_time.toString("yyyy-MM-dd HH:mm:ss")
        else:
            time_stamp = None # No time restriction
        default_time = QDateTime.currentDateTime().addDays(-1)
        selected_time = self.time_filter.dateTime()
        
        logs = fetch_filtered_logs(cart_id, position, time_stamp)

        try:
            logs = sorted(logs, key=lambda r: r.get("time_stamp"), reverse=True)
        except Exception:
            pass

        self.table.setRowCount(len(logs))
        for i, row in enumerate(logs):
            ts = row["time_stamp"]
            ts_str = ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts)
            cart_id_display = "ERROR READING" if row["cart_id"] == "0000" else row["cart_id"]
            event_type = row.get("action_type", "")  # Request or Report
            event = row.get("event", "")  # event from db (renamed from event_type)
            values = [
                cart_id_display,
                row.get("position", ""),
                event_type,
                event,
                ts_str
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                font = item.font()
                font.setPointSize(14)
                if col == 2:  # "Event Type" column
                    font.setBold(True)
                if col == 3:  # "Event" column
                    font.setBold(True)
                item.setFont(font)
                # Alternate row coloring
                if i % 2 == 0:
                    item.setBackground(Qt.white)
                else:
                    item.setBackground(QtGui.QColor("#f7fafd"))
                item.setForeground(QtGui.QBrush(QtGui.QColor("#14213d")))
                # Text alignment
                if col == 0:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
                else:
                    item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.table.setItem(i, col, item)

            # Special event coloring for diverted
            if row.get("event", "") == "diverted":
                for col in range(5):
                    item = self.table.item(i, col)
                    item.setBackground(Qt.green)
                    item.setForeground(Qt.white)

    def clear_filters(self):
        self.cart_filter.setCurrentIndex(0)
        self.station_filter.setCurrentIndex(0)
        self.time_filter.blockSignals(True)
        self.time_filter.setDateTime(QDateTime.currentDateTime().addDays(-1))
        self.time_filter.blockSignals(False)
        self.time_filter_dirty = False
        self.load_logs()
