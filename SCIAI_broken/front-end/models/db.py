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
        "database": os.getenv("MYSQL_DB", "prt_unified")
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

        # First check cart_logs for activity
        cursor.execute(
            "SELECT * FROM cart_logs WHERE cart_id = %s ORDER BY time_stamp DESC LIMIT 1",
            (cart_id,)
        )
        log_result = cursor.fetchone()

        # Also get cart info from PRTCarts (master data)
        cursor.execute(
            "SELECT barcode, destination FROM PRTCarts WHERE barcode = %s",
            (cart_id,)
        )
        cart_result = cursor.fetchone()

        cursor.close()
        conn.close()

        if log_result:
            # Return log data with destination from PRTCarts
            result = log_result
            if cart_result:
                result['destination'] = cart_result['destination']
            print(f"Cart info for {cart_id}: {result}")
            return result
        elif cart_result:
            # No log entry, but cart exists in PRTCarts - return default info
            result = {
                'cart_id': cart_result['barcode'],
                'position': 'Segment_A',
                'event_type': 'Idle',
                'time_stamp': 'No activity yet',
                'destination': cart_result['destination']
            }
            print(f"Cart info for {cart_id} (from PRTCarts): {result}")
            return result
        else:
            print(f"Cart {cart_id} not found")
            return None
    except Exception as e:
        print(f"Error fetching cart info: {e}")
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
    """Fetch all cart IDs from PRTCarts (master cart list)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT barcode FROM PRTCarts ORDER BY barcode")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row['barcode'] for row in rows]
    except Exception as e:
        print(f"Error fetching all cart IDs: {e}")
        return []

def fetch_all_carts():
    """Fetch all carts from PRTCarts with their latest position from cart_logs."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Get all carts from PRTCarts
        cursor.execute("SELECT barcode, destination FROM PRTCarts ORDER BY barcode")
        carts = cursor.fetchall()

        # Get latest position for each cart from cart_logs
        result = []
        for cart in carts:
            barcode = cart['barcode']
            cursor.execute(
                """
                SELECT position, event, time_stamp
                FROM cart_logs
                WHERE cart_id = %s
                ORDER BY time_stamp DESC
                LIMIT 1
                """,
                (barcode,)
            )
            log = cursor.fetchone()

            result.append({
                'cart_id': barcode,
                'destination': cart['destination'],
                'position': log['position'] if log else 'Segment_A',
                'event': log['event'] if log else 'Idle',
                'time_stamp': log['time_stamp'] if log else None
            })

        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error fetching all carts: {e}")
        return []