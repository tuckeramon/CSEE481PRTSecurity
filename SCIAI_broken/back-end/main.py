from time import time, sleep
from Communication.PLC import PLC
from Communication.PRTDB import PRTDB
from Communication.PLCSecurityMonitor import PLCSecurityMonitor
from Communication.CorrelationEngine import CorrelationEngine
from PRTConfig import TAG_TO_READ, STATUS_BIT, TAG_TO_WRITE, prt_get_dest_route
from Communication.PLCConfig import PRT_PLC_IP_ADDRESS, PLC_FIREWALL_ENABLED
from Communication.PLCProxyFirewall import PLCProxyFirewall
from Communication.FirewallConfig import (
    PLC_TARGET_IP, PROXY_PORT_MAP, PROXY_BIND_IP,
    WHITELIST_IPS, WHITELIST_REFRESH_INTERVAL
)
from PRTPLC import PRTPLC
from PRTConfig import BARCODE_DESTINATION_MAP
# Server and threading imports removed - now using direct database polling instead of HTTP
# DataLogger import removed - logging now done via cart_logs table in database

# Watchdog interval (seconds)
WATCHDOG_INTERVAL = 2

# Removal command poll interval (seconds)
REMOVAL_POLL_INTERVAL = 1

# Security monitoring intervals (seconds)
SECURITY_CHECK_INTERVAL = 5       # Check for mode changes, faults every 5 seconds
SECURITY_STATUS_INTERVAL = 300    # Log periodic status every 5 minutes
CORRELATION_INTERVAL = 10         # Run correlation engine every 10 seconds

# PRT PLC
prt = None


# PLC Security Monitor
security_monitor = None

# SQL Correlation Engine
correlation_engine = None

# PLC Proxy Firewall
proxy_firewall = None

# MAJOR CHANGE: Database configuration now points to unified 'prt_unified' database
# OLD: 'database': 'prtdb' - Backend had separate database from frontend
# NEW: 'database': 'prt_unified' - NEW database that doesn't affect existing databases
#
# Benefits of unified database:
# 1. Simpler architecture - only one database to manage
# 2. Data consistency - no synchronization issues between databases
# 3. Direct cart_logs population - PRTDB now writes activity logs automatically
# 4. Eliminated HTTP logging layer - no more log_server.py or WebRequester classes
#
# ARCHITECTURE CHANGE: Removed HTTP Server (Server.py)
# OLD: Frontend sent HTTP POST to localhost:2650 to update destinations/removals
# NEW: Frontend writes directly to database tables, backend polls for changes
# - PRTCarts: Frontend updates destination, backend reads when PLC requests routing
# - PRTRemoveCart: Frontend inserts commands, backend polls and processes
#
# Database contains both:
# - PRT tables (PRTSorterRequest, PRTSorterResponse, PRTSorterReport, PRTCarts, PRTRemoveCart)
# - Frontend tables (users, cart_logs)
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'prt_unified'  # NEW database - won't affect existing prtdb or prt_system
}
prtdb = PRTDB(config)

def get_destination(barcode: str, sorter_num: int):
    print(f"GET_DEST: barcode: {barcode}, sorter_num: {sorter_num}")
    #physical_dest = BARCODE_DESTINATION_MAP.get(barcode)  # Stations 1-4
    result = prtdb.get_destination_info(barcode)  # Stations 1-4
    if result is None:
        print(f"GET_DEST: barcode {barcode} not found in PRTCarts, defaulting to straight-through")
        return 0
    physical_dest = result['destination']
    dest_rt = prt_get_dest_route(physical_dest)
    dest = dest_rt[sorter_num]
    print(f"GET_DEST: barcode: {barcode}, sorter_num: {sorter_num}, physical_dest: {physical_dest}, dest_rt: {dest_rt}, dest: {dest}")
    return dest

def process_barcode(barcode: str):
    if len(barcode) != 4:
        return "0000"
    elif barcode[0] < '0' or barcode[0] > '9':
        return "0000"
    elif barcode[1] < '0' or barcode[1] > '9':
        return "0000"
    elif barcode[2] < '0' or barcode[2] > '9':
        return "0000"
    elif barcode[3] < '0' or barcode[3] > '9':
        return "0000"
    return barcode

def initialize_system():
    global prt, security_monitor, proxy_firewall

    # Start proxy firewall BEFORE any PLC connections
    if PLC_FIREWALL_ENABLED:
        print(f"FIREWALL: Initializing PLC proxy firewall...")
        proxy_firewall = PLCProxyFirewall(
            prtdb=prtdb,
            plc_target_ip=PLC_TARGET_IP,
            proxy_port_map=PROXY_PORT_MAP,
            proxy_bind_ip=PROXY_BIND_IP,
            whitelist_ips=WHITELIST_IPS
        )
        proxy_firewall.start()
        print(f"FIREWALL: Proxy active - forwarding to {PLC_TARGET_IP}")
    else:
        print("FIREWALL: Proxy firewall disabled - connecting directly to PLC")

    print(f"PRT_PLC: Connecting to PLC: {PRT_PLC_IP_ADDRESS}...")
    prt = PRTPLC()
    # HTTP Server removed - frontend now writes directly to database
    # Backend polls PRTRemoveCart for removal commands
    prt.write_tag(f'SORTER_1_REQUEST.END', 0)
    prt.write_tag(f'SORTER_2_REQUEST.END', 0)
    prt.write_tag(f'SORTER_1_REPORT.END', 0)
    prt.write_tag(f'SORTER_2_REPORT.END', 0)
    prt.send_watchdog_signal()

    # Initialize PLC Security Monitor
    # This monitors for security-relevant events: mode changes, faults, baseline deviations
    print(f"SECURITY: Initializing security monitor for PLC: {PRT_PLC_IP_ADDRESS}...")
    security_monitor = PLCSecurityMonitor(PRT_PLC_IP_ADDRESS, prtdb)
    if security_monitor.connect():
        print("SECURITY: Security monitor connected and baseline verified")
    else:
        print("SECURITY: Warning - Security monitor failed to connect (will retry)")

    # Initialize SQL Correlation Engine
    # Detects attack patterns in PLCSecurityLogs and stores alerts in PLCSecurityAlerts
    global correlation_engine
    print("CORRELATION: Initializing correlation engine...")
    correlation_engine = CorrelationEngine(prtdb)

    print("System initialized - polling database for commands...")

def process_removal_commands():
    """
    Poll PRTRemoveCart table for pending removal commands from frontend.
    Process each command by updating cart destination and notifying PLC.
    """
    commands = prtdb.fetch_pending_removal_commands()
    for cmd in commands:
        command_id = cmd['id']
        barcode = cmd['barcode']
        area = cmd['area']
        print(f"Processing removal command: cart {barcode} to area {area}")

        # Update cart destination to the removal area
        # Areas 5-9 are removal/unload areas
        prtdb.update_destination_info(barcode, area)

        # Mark command as processed (deletes from PRTRemoveCart, logs to cart_logs)
        prtdb.process_removal_command(command_id, barcode, area)


def run_system():
    initialize_system()
    # Inform the operator that only valid barcode reads will be printed
    print("Only printing valid barcode reads")
    LAST_WATCHDOG_TIME = time()
    LAST_REMOVAL_POLL_TIME = time()
    LAST_SECURITY_CHECK_TIME = time()
    LAST_SECURITY_STATUS_TIME = time()
    LAST_CORRELATION_TIME = time()
    LAST_WHITELIST_REFRESH_TIME = time()

    while (True):
        process_sorter(1)
        process_sorter(2)
        current_time = time()

        if current_time - LAST_WATCHDOG_TIME >= WATCHDOG_INTERVAL:
            prt.send_watchdog_signal()
            LAST_WATCHDOG_TIME = current_time

        # Poll for removal commands from frontend
        if current_time - LAST_REMOVAL_POLL_TIME >= REMOVAL_POLL_INTERVAL:
            process_removal_commands()
            LAST_REMOVAL_POLL_TIME = current_time

        # Security check: detect mode changes, faults, anomalies
        if current_time - LAST_SECURITY_CHECK_TIME >= SECURITY_CHECK_INTERVAL:
            if security_monitor:
                security_monitor.check_security_status()
            LAST_SECURITY_CHECK_TIME = current_time

        # Periodic security status log (for audit trail)
        if current_time - LAST_SECURITY_STATUS_TIME >= SECURITY_STATUS_INTERVAL:
            if security_monitor:
                security_monitor.log_periodic_status()
            LAST_SECURITY_STATUS_TIME = current_time

        # Run correlation engine to detect attack patterns
        if current_time - LAST_CORRELATION_TIME >= CORRELATION_INTERVAL:
            if correlation_engine:
                correlation_engine.run_correlation()
            LAST_CORRELATION_TIME = current_time

        # Refresh firewall whitelist from database
        if current_time - LAST_WHITELIST_REFRESH_TIME >= WHITELIST_REFRESH_INTERVAL:
            if proxy_firewall:
                proxy_firewall.refresh_whitelist()
            LAST_WHITELIST_REFRESH_TIME = current_time

def process_sorter(sorter_num: int):
    sorter_request = prt.read_sorter_request(sorter_num)
    if sorter_request is not None:
        print(f'Sorter_Request: {sorter_request}')
        barcode, transaction_id = sorter_request
        # Add handling for when barcode is invalid-Send it straight, log an error
        barcode = process_barcode(barcode)
        # Send PLC response FIRST — the PLC has a tight timeout before the cart
        # passes the diversion point. DB logging can wait.
        destination = get_destination(barcode, sorter_num)
        prt.send_sorter_response(sorter_num, transaction_id, destination)
        # Log to DB after response is sent (non-time-critical)
        prtdb.store_sorter_request(sorter_num, barcode, transaction_id)
        prtdb.store_sorter_response(sorter_num, transaction_id, barcode, destination)

    sorter_report = prt.read_sorter_report(sorter_num)
    if sorter_report is not None:
        barcode, active, lost, good, diverted = sorter_report
        #logger.log_data(SORTER=sorter_num, TYPE="REPORT", BARCODE=barcode, ACTIVE=active, LOST=lost, GOOD=good, DIVERTED=diverted)
        barcode = process_barcode(barcode)
        prtdb.store_sorter_report(sorter_num, barcode, active, lost, good, diverted)


def tes_system():
    print(f"PLCPrt: Connecting to PLC: {PRT_PLC_IP_ADDRESS}...")
    prt_plc = PLC(PRT_PLC_IP_ADDRESS)
    prt_plc.connect()
    print(f"PLCPrt: Successfully connected to PLC: {PRT_PLC_IP_ADDRESS}...")
    while (True):
        end_bit = prt_plc.read_tag(TAG_TO_READ + STATUS_BIT)
        print(f"End bit: {end_bit}")
        if end_bit == 1:
            data = prt_plc.read_tag(TAG_TO_READ)
            print(f"Data: {data}")
            prt_plc.write_tag(TAG_TO_READ + STATUS_BIT, 0)
            prt_plc.write_tag(TAG_TO_WRITE + '.TRANSACTION_ID', data['TRANSACTION_ID'])
            prt_plc.write_tag(TAG_TO_WRITE + '.DESTINATION', 2)
            prt_plc.write_tag(TAG_TO_WRITE + '.END', 1)
            
        
def main():
    run_system()
    #test_system()

if __name__ == "__main__":
    main()