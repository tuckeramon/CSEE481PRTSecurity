import pymysql
import getpass
from security import hash_password

def create_first_admin():
    username = input("Enter username for the first admin: ")
    password = getpass.getpass("Enter password for the first admin: ")

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
                (username, hashed_pw, 'admin')
            )
        conn.commit()
        conn.close()
        print("Admin user created.")
    except pymysql.MySQLError as e:
        print("Failed to create admin user:", e)

if __name__ == "__main__":
    create_first_admin()