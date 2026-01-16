from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QSizePolicy, QPushButton, QVBoxLayout, QInputDialog, QLineEdit, QMessageBox
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


class NavBar(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user 
        self.setFixedHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Outer layout (holds the gold background container)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Inner container that gets the gold background
        container = QWidget()
        container.setObjectName("navbar_container")
        container.setFixedHeight(100)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo = QLabel()
        pixmap = QPixmap("gui/assets/logo.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaledToHeight(150, Qt.SmoothTransformation)
            logo.setPixmap(pixmap)
        else:
            logo.setText("Logo")
        logo.setAlignment(Qt.AlignVCenter)
        logo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        layout.addWidget(logo)

        # Buttons
        self.dashboard_btn = QPushButton("PRT Dashboard")
        self.dashboard_btn.setCursor(Qt.PointingHandCursor)
        self.dashboard_btn.setCheckable(True)
        self.dashboard_btn.setChecked(True)
        layout.addWidget(self.dashboard_btn)

        self.activity_btn = QPushButton("Activity Log")
        self.activity_btn.setCursor(Qt.PointingHandCursor)
        self.activity_btn.setCheckable(True)
        layout.addWidget(self.activity_btn)

        # Add admin-only button
        if user["role"] == "admin":
            self.manage_users_btn = QPushButton("Manage Users")
            self.manage_users_btn.setCursor(Qt.PointingHandCursor)
            self.manage_users_btn.setCheckable(True)
            layout.addWidget(self.manage_users_btn)

        else:
            self.manage_users_btn = None

        layout.addStretch()
        outer_layout.addWidget(container)

        # Style only the container
        self.setStyleSheet("""
            QWidget#navbar_container {
                background-color: #EAAA00;
                border-bottom: 2px solid #FFFFFF;
            }
            QWidget {
                background-color: #EAAA00;
                border-bottom: 2px solid #FFFFFF;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 8px 20px;
                margin: 10px;
            }

            QPushButton:hover {
                background-color: #ffc600;
                color: #002855;
                border-radius: 5px;
            }

            QPushButton:checked {
                background-color: white;
                color: #002855;
                border-radius: 5px;
            }
            QLineEdit {
                font-size: 16px;
                border: 1px solid black;
                background-color: transparent;
                border-radius: 5px;
                padding: 5px;
                color: white;
            }
            QInputDialog:getText {
                background-color: #EAAA00;
                color: #002855;
                font-size: 16px; 
            }
        """)

        # Switch state behavior
        self.dashboard_btn.clicked.connect(self.set_dashboard_active)
        self.activity_btn.clicked.connect(self.set_activity_active)

    def set_dashboard_active(self):
        self.dashboard_btn.setChecked(True)
        self.activity_btn.setChecked(False)
        if self.manage_users_btn:
            self.manage_users_btn.setChecked(False)

    def set_activity_active(self):
        self.dashboard_btn.setChecked(False)
        self.activity_btn.setChecked(True)
        if self.manage_users_btn:
            self.manage_users_btn.setChecked(False)

    def set_manage_users_active(self):
        if self.manage_users_btn:
            self.dashboard_btn.setChecked(False)
            self.activity_btn.setChecked(False)
            self.manage_users_btn.setChecked(True)
