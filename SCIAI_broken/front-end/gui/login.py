from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
)
import pymysql
from security import check_password
from typing import Dict
from models.db import get_connection
import socket

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(300, 180)
        self.logged_user = None

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.attempt_login)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Username: "))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password: "))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)

    def attempt_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        def _log_attempt(u, ok):
            try:
                conn = get_connection()
                cursor = conn.cursor()
                try:
                    source_ip = socket.gethostbyname(socket.gethostname())
                    if source_ip.startswith('127.') or source_ip == '0.0.0.0':
                        source_ip = '127.0.0.1'
                except Exception:
                    source_ip = '127.0.0.1'

                cursor.execute(
                    "INSERT INTO PRTLoginAttempts (username, source_ip, status) VALUES (%s, %s, %s)",
                    (u, source_ip, 'success' if ok else 'failure')
                )
                conn.commit()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Error logging login attempt: {e}")

        try:
            # Use centralized DB connection (reads credentials from env via models.db.load_config)
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
            conn.close()

            if user and check_password(password, user['password_hash']):
                _log_attempt(username, True)
                self.logged_user = user
                self.accept()
            else:
                _log_attempt(username, False)
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Database Error", str(e))
