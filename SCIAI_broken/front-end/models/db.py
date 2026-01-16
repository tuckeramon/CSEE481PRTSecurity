# db.py
import pymysql
import os
from dotenv import load_dotenv
import datetime

# Load environment variables
load_dotenv()

# Allowed positions (enum values)
ALLOWED_POSITIONS = {
    'Station_1', 'Station_2', 'Station_3', 'Station_4',
    'Segment_A', 'Segment_B', 'Segment_C', 'Segment_D',
    'Segment_E', 'Segment_F'
}
EVENT_MAP = {
    "0000": "Not Diverted",
    "0010": "Lost",
    "0100": "Diverted",
    "0101": "Good & Diverted"
}

# Load MySQL config
def load_config():
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "root"),
        "database": os.getenv("MYSQL_DB", "prt_system")
    }

# Connect to MySQL
def get_connection():
    config = load_config()
    #print("🔍 db.py: Running get_connection()")
    #print(f"Connecting to MySQL with config: {config}")
    try:
        conn = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            connect_timeout=5,
            cursorclass=pymysql.cursors.DictCursor
        )
        #print("✅ MySQL connection established.")
        #print("🟢 get_connection(): returning connection object")
        return conn
    except Exception as err:
        import traceback
        print(f"❌ Database connection failed: {err}")
        traceback.print_exc()
        raise

# Log a cart event with validation
def log_event(cart_id, position, event, action_type=None):
    if position not in ALLOWED_POSITIONS:
        raise ValueError(f"Invalid position: {position}")

    event_str = EVENT_MAP.get(event, event)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if action_type is not None:
            cursor.execute(
                "INSERT INTO cart_logs (cart_id, position, event, action_type) VALUES (%s, %s, %s, %s)",
                (cart_id, position, event, action_type)
            )
        else:
            cursor.execute(
                "INSERT INTO cart_logs (cart_id, position, event) VALUES (%s, %s, %s)",
                (cart_id, position, event)
            )
        conn.commit()
        cursor.close()
        conn.close()
        print(f"📦 Logged event: {cart_id}, {position}, {event}, {action_type}")
    except Exception as e:
        print(f"❌ Error logging event: {e}")

# Get latest info
def get_cart_info(cart_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM cart_logs WHERE cart_id = %s ORDER BY time_stamp DESC LIMIT 1",
            (cart_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"📋 Cart info for {cart_id}: {result}")
        return result
    except Exception as e:
        print(f"❌ Error fetching cart info: {e}")
        return None

def remove_cart_request(cart_id, area):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cart_logs (cart_id, position, event, action_type, time_stamp) VALUES (%s, %s, %s, %s, %s)",
            (cart_id, f"Remove_Area_{area}", "Remove Cart", "Request", datetime.datetime.now())
        )
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Logged remove cart request: {cart_id}, Area: {area}")
    except Exception as e:
        print(f"Error logging remove cart request: {e}")

def fetch_activity_logs(limit=100):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT cart_id, position, action_type, event, time_stamp
            FROM cart_logs
            ORDER BY time_stamp DESC
            LIMIT %s
            """,
            (limit,)
        )
        logs = cursor.fetchall()
        cursor.close()
        conn.close()
        #print(f"Fetched {len(logs)} activity log entries.")
        return logs
    except Exception as e:
        print(f"❌ Error fetching activity logs: {e}")
        return []
    
def fetch_filtered_logs(cart_id=None, position=None, since_time=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT cart_id, position, action_type, event, time_stamp
            FROM cart_logs
        """
        conditions = []
        params = []
        if cart_id:
            conditions.append("cart_id = %s")
            params.append(cart_id)
        if position:
            conditions.append("position = %s")
            params.append(position)
        if since_time:
            conditions.append("time_stamp >= %s")
            params.append(since_time)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY time_stamp DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        print(f"Fetched {len(rows)} filtered activity log entries.")
        return rows
    except Exception as e:
        print(f"Error fetching filtered logs: {e}")
        return []
    
def fetch_all_cart_ids():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT cart_id FROM cart_logs ORDER BY cart_id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row['cart_id'] for row in rows]
    except Exception as e:
        print(f"Error fetching all cart IDs: {e}")
        return []