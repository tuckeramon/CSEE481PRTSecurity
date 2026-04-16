from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSizePolicy, QStackedWidget, QMessageBox,
    QStatusBar, QLabel,
)
from PyQt5.QtGui import QColor
from gui.navbar import NavBar
from gui.home_view import HomeView
from gui.activity_log_view import ActivityLogView
from gui.security_log_view import SecurityLogView
from models.db import get_connection
from .add_user import AddUser
from gui.manage_users_view import ManageUsersView
from PyQt5.QtWidgets import QApplication
import sys

class MainWindow(QMainWindow):
    def __init__(self, db_conn, user, tunnel_manager=None):
        super().__init__()
        self.resize(1400, 900)
        self.db_conn = db_conn
        self.user = user
        self._tunnel_manager = tunnel_manager

        try:
            role = self.user.get("role", "viewer")

            # Create navigation bar
            self.navbar = NavBar(self.user)
            self.navbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            # Create views
            self.home_view = HomeView()
            self.activity_view = ActivityLogView(self.db_conn)
            self.security_view = SecurityLogView(self.user) if role in ("admin", "operator") else None
            self.manage_users_view = ManageUsersView() if role == "admin" else None

            # Page stack
            self.stack = QStackedWidget()
            self.stack.addWidget(self.home_view)
            self.stack.addWidget(self.activity_view)
            if self.security_view:
                self.stack.addWidget(self.security_view)
            if self.manage_users_view:
                self.stack.addWidget(self.manage_users_view)

            # Connect navbar buttons
            self.navbar.dashboard_btn.clicked.connect(lambda: [self.stack.setCurrentIndex(0), self.navbar.set_dashboard_active()])
            self.navbar.activity_btn.clicked.connect(lambda: [self.stack.setCurrentIndex(1), self.navbar.set_activity_active()])
            if self.navbar.security_btn and self.security_view:
                self.navbar.security_btn.clicked.connect(lambda: [self.stack.setCurrentWidget(self.security_view), self.navbar.set_security_active()])
            if self.navbar.manage_users_btn and self.manage_users_view:
                self.navbar.manage_users_btn.clicked.connect(lambda: [self.stack.setCurrentWidget(self.manage_users_view), self.navbar.set_manage_users_active()])

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

            # Status bar — SSH tunnel indicator
            self._ssh_status_label = QLabel()
            self._ssh_status_label.setStyleSheet(
                "color: #44ff88; font-size: 11px; padding: 0 8px;"
            )
            status_bar = QStatusBar()
            status_bar.setStyleSheet(
                "QStatusBar { background-color: #001533; color: #99aacc; font-size: 11px; }"
            )
            status_bar.addPermanentWidget(self._ssh_status_label)
            self.setStatusBar(status_bar)
            self._update_ssh_status()

        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.exit(1)

    def _update_ssh_status(self):
        if self._tunnel_manager is None:
            self._ssh_status_label.setText("SSH: not configured")
            self._ssh_status_label.setStyleSheet("color: #aaaacc; font-size: 11px; padding: 0 8px;")
        elif self._tunnel_manager.is_active:
            port = self._tunnel_manager.local_port
            self._ssh_status_label.setText(f"SSH: connected  (:{port} → 192.168.1.222)")
            self._ssh_status_label.setStyleSheet("color: #44ff88; font-size: 11px; padding: 0 8px;")
        else:
            self._ssh_status_label.setText("SSH: disconnected")
            self._ssh_status_label.setStyleSheet("color: #ff6666; font-size: 11px; padding: 0 8px;")

    def closeEvent(self, event):
        # Stop any running background worker thread so the process can exit cleanly
        if self.security_view is not None:
            worker = self.security_view._worker
            if worker is not None and worker.isRunning():
                worker.quit()
                worker.wait()
        if self._tunnel_manager is not None:
            self._tunnel_manager.stop()
        event.accept()
        QApplication.quit()

    def open_add_user(self):
        dialog = AddUser()
        dialog.exec_()