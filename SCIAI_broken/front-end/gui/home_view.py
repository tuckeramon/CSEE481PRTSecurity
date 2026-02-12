from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFrame, QVBoxLayout, QLabel, QSizePolicy, QPushButton, QComboBox
from PyQt5.QtCore import Qt
from gui.track_view import TrackView
from models.db import get_cart_info, remove_cart_request
from models.api import send_cart_to_station
from models.api import remove_cart

class HomeView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Outer vertical layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Title label
        label = QLabel("Live map & Control Panel")
        label.setStyleSheet(
        """
            font-size: 25px;
            color: #002855;
            font-weight: bold;
            color: white;
        """)
        main_layout.addWidget(label)

        # Horizontal layout for map and panel
        h_layout = QHBoxLayout()
        h_layout.setSpacing(20)

        # Live Track Map
        self.track_view = TrackView()
        self.track_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.track_view.cart_selected.connect(self.display_cart_info)

        # Side panel for cart info
        self.panel_frame = QFrame()
        self.panel_frame.setMinimumSize(300, 400)
        self.panel_frame.setStyleSheet(
            """
            background-color: #EAAA00;
            border: 2px solid #002855;
            border-radius: 6px;
            """)

        self.info_label = QLabel("Select a cart to view details.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            """
            padding: 10px;
            font-size: 25px;
            color: white;
            """)

        panel_layout = QVBoxLayout()

        # Cart selection dropdown
        cart_select_label = QLabel("Select Cart:")
        cart_select_label.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            color: white;
            border: 2px solid #002855;
            border-radius: 6px;
            padding: 6px 12px;
            """
        )
        panel_layout.addWidget(cart_select_label)

        self.cart_dropdown = QComboBox()
        self.cart_dropdown.addItem("")
        self.cart_dropdown.setStyleSheet(
            """
            QComboBox {
                background-color: white;
                color: #002855;
                border: 2px solid #002855;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #EAAA00;
                selection-color: black;
                border: none;
                font-size: 16px;
                padding: 6px;
                outline: 0;
            }
            """
        )
        panel_layout.addWidget(self.cart_dropdown)

        info_title = QLabel("<b>Cart Information</b>")
        info_title.setAlignment(Qt.AlignCenter)
        info_title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: white;
            border-radius: 6px;
            padding: 10px;
            """)
        #panel_layout.addWidget(self.cart_status)
        panel_layout.addWidget(info_title)
        panel_layout.addWidget(self.info_label)

        # Dropdown Label (Station Destination)
        station_label = QLabel("Select Station Destination:")
        station_label.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            color: white;
            border: 2px solid #002855;
            border-radius: 6px;
            padding: 6px 12px;
            """
        )
        panel_layout.addWidget(station_label)

        # Dropdown for stations
        self.station_dropdown = QComboBox()
        self.station_dropdown.addItems(["","Station 1", "Station 2", "Station 3", "Station 4"])
        self.station_dropdown.setEnabled(False)
        self.station_dropdown.setStyleSheet(
            """
            QComboBox:enabled {
                background-color: white;
                color: #002855;
                border: 2px solid #002855;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 16px;
            }
            QComboBox:disabled {
                background-color: #f5e6b5;
                color: #888;
                border: 2px solid #002855;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 16px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #EAAA00;
                selection-color: black;
                border: none;
                font-size: 16px;
                padding: 6px;
                outline: 0;
                }
            """
        )
        panel_layout.addWidget(self.station_dropdown)

        # Dropdown label (Unload drop-off area)
        area_label = QLabel("Select Unload Drop-off Area:")
        area_label.setStyleSheet(
            """
            font-size: 16px;
            font-weight: bold;
            color: white;
            border: 2px solid #002855;
            border-radius: 6px;
            padding: 6px 12px;
            """
        )
        panel_layout.addWidget(area_label)

        # Dropdown for areas
        self.area_dropdown = QComboBox()
        self.area_dropdown.addItems(["","Area 5", "Area 6", "Area 7", "Area 8", "Area 9"])
        self.area_dropdown.setEnabled(False)
        self.area_dropdown.setStyleSheet(
            """
            QComboBox:enabled {
                background-color: white;
                color: #002855;
                border: 2px solid #002855;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 16px;
                }
            QComboBox:disabled {
                background-color: #f5e6b5;
                color: #888;
                border: 2px solid #002855;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 16px;
                }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #EAAA00;
                selection-color: black;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                padding: 6px;
                outline: none;
                }
            """
        )

        panel_layout.addWidget(self.area_dropdown)

        # Send button
        self.send_button = QPushButton("Send Cart to Station")
        self.send_button.setEnabled(False)
        self.send_button.setStyleSheet(
            """
            QPushButton:enabled {
                background-color: white;
                color: #002855;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:disabled {
                background-color: #f5e6b5;
                color: #888;
                border-radius: 6px;
                padding: 6px;
            }
            """
        )

        # Remove active cart button
        self.remove_button = QPushButton("Remove Active Cart")
        self.remove_button.setEnabled(False)
        self.remove_button.setStyleSheet(
            """
            QPushButton:enabled {
                background-color: white;
                color: #002855;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:disabled {
                background-color: #f5e6b5;
                color: #888;
                border-radius: 6px;
                padding: 6px;
            }
            """
        )

        # Create horizontal layout for the two buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(10)  # Optional: space between buttons
        button_row.addWidget(self.send_button)
        button_row.addWidget(self.remove_button)

        # Add the row to the panel layout
        panel_layout.addLayout(button_row)


        panel_layout.addStretch()
        self.panel_frame.setLayout(panel_layout)

        h_layout.addWidget(self.track_view, 3)
        h_layout.addWidget(self.panel_frame, 2)

        main_layout.addLayout(h_layout)
        self.setLayout(main_layout)

        self.send_button.clicked.connect(self.send_cart_to_station_clicked)
        self.remove_button.clicked.connect(self.remove_active_cart_clicked)

        # Connect cart dropdown selection to map highlight
        self.cart_dropdown.currentIndexChanged.connect(self.on_cart_dropdown_changed)

        # Connect map click to update cart dropdown
        self.track_view.cart_selected.connect(self.sync_cart_dropdown_to_selection)

        # Connect cart list refresh to repopulate dropdown
        self.track_view.carts_updated.connect(self.refresh_cart_dropdown)

        # Connect dropdown changes to button state updates
        self.station_dropdown.currentIndexChanged.connect(self.buttons_enabled)
        self.area_dropdown.currentIndexChanged.connect(self.buttons_enabled)

        # Initial button state
        self.buttons_enabled()

    def display_cart_info(self, cart_id):
        data = get_cart_info(cart_id)
        if data:
            self.info_label.setText(
                f"<b>Cart ID:</b> {data['cart_id']}<br>"
                f"<b>Status:</b> {data.get('event_type', 'N/A')}<br>"
                f"<b>Location:</b> {data.get('position', 'Unknown')}<br>"
                f"<b>Time:</b> {data['time_stamp']}"
            )
            self.station_dropdown.setEnabled(True)
            self.area_dropdown.setEnabled(True)
        else:
            self.info_label.setText(f"Cart '{cart_id}' has no recent data.")
            self.station_dropdown.setEnabled(False)
        self.buttons_enabled()

    def buttons_enabled(self, *_):
        cart_selected = hasattr(self, 'track_view') and getattr(self.track_view, 'selected_cart_id', None)
        self.send_button.setEnabled(
            bool(cart_selected) and self.station_dropdown.isEnabled() and self.station_dropdown.currentIndex() > 0
        )
        self.remove_button.setEnabled(
            bool(cart_selected) and self.area_dropdown.isEnabled() and self.area_dropdown.currentIndex() > 0
        )

    def send_cart_to_station_clicked(self):
        if not hasattr(self, 'track_view') or not self.track_view.selected_cart_id:
            return
        if self.station_dropdown.currentIndex() <= 0:
            return
        cart_id = self.track_view.selected_cart_id
        station_index = self.station_dropdown.currentIndex()
        station_id = f"Station_{station_index}"
        send_cart_to_station(cart_id, station_id)
        self.info_label.setText(f"Sent cart {cart_id} to {station_id}.")
        self.buttons_enabled()

    def remove_active_cart_clicked(self):
        if not hasattr(self, 'track_view') or not self.track_view.selected_cart_id:
            return
        if self.area_dropdown.currentIndex() <= 0:
            return
        cart_id = self.track_view.selected_cart_id
        area_text = self.area_dropdown.currentText()
        area = area_text.split()[-1] if area_text else ""
        remove_cart(cart_id, area)
        self.info_label.setText(f"Removed cart {cart_id} to area {area}.")
        self.buttons_enabled()

    def on_cart_dropdown_changed(self, index):
        """When user selects a cart from the dropdown, highlight it on the map."""
        cart_id = self.cart_dropdown.currentText()
        if not cart_id:
            return
        self.track_view.selected_cart_id = cart_id
        self.track_view.update()
        self.display_cart_info(cart_id)

    def sync_cart_dropdown_to_selection(self, cart_id):
        """When user clicks a dot on the map, update the dropdown to match."""
        self.cart_dropdown.blockSignals(True)
        idx = self.cart_dropdown.findText(cart_id)
        if idx >= 0:
            self.cart_dropdown.setCurrentIndex(idx)
        self.cart_dropdown.blockSignals(False)

    def refresh_cart_dropdown(self, cart_ids):
        """Repopulate the cart dropdown when the cart list refreshes."""
        previous = self.cart_dropdown.currentText()
        self.cart_dropdown.blockSignals(True)
        self.cart_dropdown.clear()
        self.cart_dropdown.addItem("")
        for cid in sorted(cart_ids):
            self.cart_dropdown.addItem(cid)
        # Restore previous selection if still present
        idx = self.cart_dropdown.findText(previous)
        if idx >= 0:
            self.cart_dropdown.setCurrentIndex(idx)
        self.cart_dropdown.blockSignals(False)
    