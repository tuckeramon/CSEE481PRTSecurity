import sys
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton,
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QColor

from gui.main_window import MainWindow
from models.db import get_connection
from gui.login import LoginWindow
from models.ssh_tunnel import SSHTunnelManager


class _TunnelWorker(QThread):
    status_signal = pyqtSignal(str, str)   # (message, status)
    finished_signal = pyqtSignal(bool)

    def __init__(self, manager):
        super().__init__()
        self._manager = manager

    def run(self):
        success = self._manager.start()
        self.finished_signal.emit(success)


class SSHStartupDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.tunnel_manager = SSHTunnelManager()
        self._success = False
        self._worker = None
        self._setup_ui()
        # Start connecting immediately after the event loop begins
        QTimer.singleShot(100, self._start_connection)

    def _setup_ui(self):
        self.setWindowTitle("PRT Security System — Connecting")
        self.setFixedSize(520, 310)
        self.setStyleSheet("background-color: #002855; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        title = QLabel("PRT Security System")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #EAAA00;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Establishing SSH tunnel to Raspberry Pi (192.168.1.222)…")
        subtitle.setStyleSheet("font-size: 11px; color: #99aacc;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        self.log_list = QListWidget()
        self.log_list.setStyleSheet("""
            QListWidget {
                background-color: #001533;
                color: #ccddff;
                font-family: Consolas, monospace;
                font-size: 11px;
                border: 1px solid #EAAA00;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item { padding: 1px 4px; }
        """)
        self.log_list.setFixedHeight(150)
        layout.addWidget(self.log_list)

        self.status_label = QLabel("Initializing…")
        self.status_label.setStyleSheet("font-size: 11px; color: #EAAA00;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.retry_btn = QPushButton("Retry")
        self.retry_btn.setStyleSheet(
            "background-color: #EAAA00; color: #002855; font-weight: bold; padding: 6px 20px;"
        )
        self.retry_btn.hide()
        self.retry_btn.clicked.connect(self._start_connection)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setStyleSheet("background-color: #444; color: white; padding: 6px 20px;")
        self.exit_btn.clicked.connect(self.reject)

        btn_row.addWidget(self.retry_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.exit_btn)
        layout.addLayout(btn_row)

    def _start_connection(self):
        self.retry_btn.hide()
        self.log_list.clear()
        self._add_log("Starting SSH tunnel…", "#99aacc")

        self._worker = _TunnelWorker(self.tunnel_manager)
        # Wire the manager's callback to emit through the worker's signal
        self.tunnel_manager.set_callback(self._worker.status_signal.emit)
        self._worker.status_signal.connect(self._on_status)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.start()

    def _on_status(self, message, status):
        color_map = {
            "CONNECTED": "#44ff88",
            "FAILED":    "#ff6666",
            "WARNING":   "#ffbb44",
            "DISCONNECTED": "#aaaacc",
        }
        color = color_map.get(status, "#99aacc")
        self._add_log(message, color)
        self.status_label.setText(message)

    def _add_log(self, message, color="#99aacc"):
        item = QListWidgetItem(f"  {message}")
        item.setForeground(QColor(color))
        self.log_list.addItem(item)
        self.log_list.scrollToBottom()

    def _on_finished(self, success):
        self._success = success
        if success:
            self._add_log("Ready — loading login…", "#44ff88")
            QTimer.singleShot(700, self.accept)
        else:
            self._add_log("Connection failed. Check SSH config and try again.", "#ff6666")
            self.status_label.setText("Connection failed.")
            self.retry_btn.show()

    @property
    def success(self):
        return self._success


def main():
    app = QApplication(sys.argv)

    # ── Step 1: SSH tunnel ────────────────────────────────────────────────────
    startup = SSHStartupDialog()
    if startup.exec_() != QDialog.Accepted or not startup.success:
        sys.exit(0)

    tunnel_manager = startup.tunnel_manager

    # ── Step 2: Login ─────────────────────────────────────────────────────────
    login_dialog = LoginWindow()
    result = login_dialog.exec_()
    success = result == LoginWindow.Accepted and login_dialog.logged_user

    if not success:
        tunnel_manager.stop()
        print("Login failed or cancelled.")
        sys.exit(0)

    # ── Step 3: Main window ───────────────────────────────────────────────────
    db_conn = get_connection()
    window = MainWindow(db_conn, login_dialog.logged_user, tunnel_manager)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
