from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSizePolicy, QStackedWidget, QMessageBox
)
from gui.navbar import NavBar
from gui.home_view import HomeView
from gui.activity_log_view import ActivityLogView 
from models.db import get_connection
from .add_user import AddUser
from gui.manage_users_view import ManageUsersView
import sys

class MainWindow(QMainWindow):
    def __init__(self, db_conn, user):
        super().__init__()
        self.resize(1400, 900)
        self.db_conn = db_conn
        self.user = user

        try:
            # Create navigation bar
            self.navbar = NavBar(self.user)
            if self.navbar.manage_users_btn:
                self.navbar.manage_users_btn.clicked.connect(lambda: [self.stack.setCurrentWidget(self.manage_users_view), self.navbar.set_manage_users_active()])
            self.navbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # Create views
            self.home_view = HomeView()
            self.activity_view = ActivityLogView(self.db_conn)
            self.manage_users_view = ManageUsersView()

            # Page stack
            self.stack = QStackedWidget()
            self.stack.addWidget(self.home_view)
            self.stack.addWidget(self.activity_view)
            self.stack.addWidget(self.manage_users_view)

            # Connect navbar buttons
            self.navbar.dashboard_btn.clicked.connect(lambda: [self.stack.setCurrentIndex(0), self.navbar.set_dashboard_active()])
            self.navbar.activity_btn.clicked.connect(lambda: [self.stack.setCurrentIndex(1), self.navbar.set_activity_active()])

            # Create main layout
            central_widget = QWidget()
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(self.navbar)
            layout.addWidget(self.stack)

            central_widget.setLayout(layout)
            self.setCentralWidget(central_widget)

            # Set background color
            self.setStyleSheet("background-color: #002855;")

        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def open_add_user(self):
        dialog = AddUser()
        dialog.exec_()