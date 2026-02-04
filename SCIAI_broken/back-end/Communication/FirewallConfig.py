"""
Firewall Configuration for PLC Proxy Firewall

Static whitelist and proxy configuration.
The proxy also loads dynamic entries from PLCFirewallWhitelist table.
"""

# Real PLC IP address (the proxy forwards whitelisted traffic here)
PLC_TARGET_IP = '192.168.1.51'

# Ports to proxy
PROXY_PORTS = [44818, 502]

# IP to bind proxy listeners on
PROXY_BIND_IP = '0.0.0.0'

# Static IP whitelist - these IPs are ALWAYS allowed
WHITELIST_IPS = {
    '127.0.0.1',           # Localhost (back-end application)
    '192.168.1.70',        # HMI (SCADALTs)
    '192.168.1.30',        # MySQL DB server
    '192.168.1.20',        # Blue team SIEM
    # '192.168.1.10',      # Kali red team - INTENTIONALLY NOT WHITELISTED
    # '192.168.1.200',     # Schneider switch - add only if needed
}

# How often to refresh the whitelist from the database (seconds)
WHITELIST_REFRESH_INTERVAL = 60

# Whether to log allowed connections (can be noisy)
LOG_ALLOWED_CONNECTIONS = True

# Protocol names for logging
PORT_PROTOCOL_MAP = {
    44818: 'EtherNet/IP',
    502: 'Modbus/TCP'
}
