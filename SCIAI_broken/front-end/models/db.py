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
    'Segment_E', 'Segment_F',
    # Removal/unload areas (used when removing carts from system)
    'Remove_Area_5', 'Remove_Area_6', 'Remove_Area_7',
    'Remove_Area_8', 'Remove_Area_9'
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

def update_cart_destination(barcode, destination):
    """
    Update cart destination directly in PRTCarts table.
    Backend will read this when PLC requests routing info.

    :param barcode: Cart barcode (e.g., "0001")
    :param destination: Station number (1-4)
    :return: True on success, False on failure
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE PRTCarts SET destination = %s WHERE barcode = %s",
            (destination, barcode)
        )
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        if affected > 0:
            print(f"Updated destination for cart {barcode} to station {destination}")
            return True
        else:
            print(f"Cart {barcode} not found in PRTCarts")
            return False
    except Exception as e:
        print(f"Error updating cart destination: {e}")
        return False

def insert_remove_cart_command(barcode, area):
    """
    Insert removal command into PRTRemoveCart table.
    Backend will poll this table and process removal requests.

    :param barcode: Cart barcode (e.g., "0001")
    :param area: Removal area (5-9)
    :return: True on success, False on failure
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO PRTRemoveCart (barcode, area) VALUES (%s, %s)",
            (barcode, area)
        )
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Inserted removal command for cart {barcode} to area {area}")
        return True
    except Exception as e:
        print(f"Error inserting removal command: {e}")
        return False


# =========================================================================
# SECURITY DASHBOARD QUERY FUNCTIONS
# =========================================================================

def fetch_security_logs(severity=None, event_type=None, plc_ip=None, since_time=None, limit=500):
    """Fetch security events from PLCSecurityLogs with optional filters."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT id, plc_ip, plc_name, event_type, severity, event_code,
                   event_message, previous_state, current_state, plc_timestamp, timestamp
            FROM PLCSecurityLogs
        """
        conditions = []
        params = []
        if severity:
            conditions.append("severity = %s")
            params.append(severity)
        if event_type:
            conditions.append("event_type = %s")
            params.append(event_type)
        if plc_ip:
            conditions.append("plc_ip = %s")
            params.append(plc_ip)
        if since_time:
            conditions.append("timestamp >= %s")
            params.append(since_time)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching security logs: {e}")
        return []


def fetch_security_alerts(severity=None, event_type=None, plc_ip=None, acknowledged=None, since_time=None, limit=200):
    """Fetch correlated alerts from PLCSecurityAlerts with optional filters."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT id, alert_id, rule_id, rule_level, rule_description,
                   plc_ip, event_type, severity, event_message,
                   matched_event_count, time_window_seconds,
                   acknowledged, acknowledged_by, acknowledged_at, detected_at
            FROM PLCSecurityAlerts
        """
        conditions = []
        params = []
        if severity:
            conditions.append("severity = %s")
            params.append(severity)
        if event_type:
            conditions.append("event_type = %s")
            params.append(event_type)
        if plc_ip:
            conditions.append("plc_ip = %s")
            params.append(plc_ip)
        if acknowledged is not None:
            conditions.append("acknowledged = %s")
            params.append(1 if acknowledged else 0)
        if since_time:
            conditions.append("detected_at >= %s")
            params.append(since_time)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY detected_at DESC LIMIT %s"
        params.append(limit)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching security alerts: {e}")
        return []


def fetch_security_summary_stats():
    """Fetch summary counts for the security dashboard stat cards."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        stats = {}

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM PLCSecurityLogs WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)"
        )
        stats["total_events_24h"] = cursor.fetchone()["cnt"]

        cursor.execute("""
            SELECT severity, COUNT(*) AS cnt
            FROM PLCSecurityLogs
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            GROUP BY severity
        """)
        severity_counts = {row["severity"]: row["cnt"] for row in cursor.fetchall()}
        stats["critical_count"] = severity_counts.get("CRITICAL", 0)
        stats["error_count"] = severity_counts.get("ERROR", 0)
        stats["warning_count"] = severity_counts.get("WARNING", 0)
        stats["info_count"] = severity_counts.get("INFO", 0)

        cursor.execute(
            "SELECT COUNT(*) AS cnt FROM PLCSecurityAlerts WHERE acknowledged = 0"
        )
        stats["unacknowledged_alerts"] = cursor.fetchone()["cnt"]

        cursor.close()
        conn.close()
        return stats
    except Exception as e:
        print(f"Error fetching security summary stats: {e}")
        return {
            "total_events_24h": 0, "critical_count": 0, "error_count": 0,
            "warning_count": 0, "info_count": 0, "unacknowledged_alerts": 0
        }


def acknowledge_security_alert(alert_id, acknowledged_by=None):
    """Mark a correlated alert as acknowledged. Returns True on success."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE PLCSecurityAlerts
            SET acknowledged = 1,
                acknowledged_by = %s,
                acknowledged_at = NOW()
            WHERE id = %s AND acknowledged = 0
            """,
            (acknowledged_by, alert_id)
        )
        affected = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return affected > 0
    except Exception as e:
        print(f"Error acknowledging alert: {e}")
        return False


def fetch_distinct_plc_ips():
    """Fetch all distinct PLC IPs from security logs for the filter dropdown."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT plc_ip FROM PLCSecurityLogs ORDER BY plc_ip")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [row["plc_ip"] for row in rows]
    except Exception as e:
        print(f"Error fetching PLC IPs: {e}")
        return []