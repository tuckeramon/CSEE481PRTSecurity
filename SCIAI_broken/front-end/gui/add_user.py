from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox
from security import hash_password
import pymysql

class AddUser(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add User")
        self.setMinimumWidth(300)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.role_input = QComboBox()
        self.role_input.addItems(["admin", "operator", "viewer"])

        self.create_btn = QPushButton("Create User")
        self.create_btn.clicked.connect(self.create_user)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Username: "))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password: "))
        layout.addWidget(self.password_input)
        layout.addWidget(QLabel("Role: "))
        layout.addWidget(self.role_input)
        layout.addWidget(self.create_btn)

        self.setLayout(layout)

    def create_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_input.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
            return
        
        hashed_pw = hash_password(password)
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
                cursor.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                    (username, hashed_pw, role)
                )
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", f"User '{username}' created successfully.")
            self.accept()

        except pymysql.MySQLError as e:
            QMessageBox.critical(self, "Database Error", str(e))