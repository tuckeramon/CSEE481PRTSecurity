from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from models.db import get_connection
from gui.login import LoginWindow
import sys

def main():
    app = QApplication(sys.argv)

    # Show the login dialog first
    login_dialog = LoginWindow()
    result = login_dialog.exec_()

    success = (result == LoginWindow.Accepted and login_dialog.logged_user)

    if success:
        db_conn = get_connection()
        window = MainWindow(db_conn, login_dialog.logged_user)
        window.show()
        sys.exit(app.exec_())
    else:
        print("Login failed or cancelled.")
        sys.exit()

if __name__ == "__main__":
    main()