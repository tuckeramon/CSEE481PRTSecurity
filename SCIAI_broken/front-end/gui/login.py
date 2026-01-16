from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
)
import pymysql
from security import check_password
from typing import Dict
from models.db import get_connection

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

        try:
            conn = pymysql.connect(
                host='localhost',
                user='root',
                password='root',
                database='prt_system',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
            conn.close()

            if user and check_password(password, user['password_hash']):
                self.logged_user = user
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", "Invalid username or password.")
        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Database Error", str(e))
