# gui/manage_users_view.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHBoxLayout
from PyQt5.QtCore import Qt
from models.db import get_connection
import pymysql.cursors

class ManageUsersView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title = QPushButton("Create New User")
        title.setStyleSheet("font-size: 18px; background-color: white; color: #002855;")
        title.clicked.connect(self.open_create_user_dialog)
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Username", "Role", "Created At", ""])
        self.table.setStyleSheet("background-color: white; color: #002855;")
        layout.addWidget(self.table)

        self.load_users()

    def load_users(self):
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT id, username, role, created_at FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()

        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(user["username"]))
            self.table.setItem(row, 1, QTableWidgetItem(user["role"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(user["created_at"])))

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #e63946; color: white;")

            if user["role"].lower() == "admin":
                delete_btn.setEnabled(False)
            else:
                delete_btn.clicked.connect(lambda _, uid=user["id"]: self.delete_user(uid))

            self.table.setCellWidget(row, 3, delete_btn)

    def delete_user(self, user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        cursor.close()
        conn.close()
        self.load_users()

    def open_create_user_dialog(self):
        from .add_user import AddUser
        self.create_user_dialog = AddUser()
        if self.create_user_dialog.exec_() == 1:
            self.load_users()
        
