import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "127.0.0.1"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "root"),
            database=os.getenv("MYSQL_DB", "prt_system"),
            connection_timeout=5
        )
        print("✅ Connected successfully!")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        for table in cursor.fetchall():
            print(f"📦 Table: {table[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        import traceback
        print("❌ Error:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
