"""
Firewall Configuration for PLC Proxy Firewall

Static whitelist and proxy configuration.
The proxy also loads dynamic entries from PLCFirewallWhitelist table.

The proxy listens on ALTERNATE ports to avoid conflicting with the real PLC
or Docker port mappings. External hosts that should go through the firewall
connect to the proxy ports, which are forwarded to the real PLC ports.

    Proxy port 34818  ->  PLC port 44818 (EtherNet/IP)
    Proxy port 1502   ->  PLC port 502   (Modbus/TCP)
"""

# Real PLC IP address (the proxy forwards whitelisted traffic here)
PLC_TARGET_IP = '192.168.1.51'

# Proxy listen port -> real PLC target port
# Keys are what the proxy binds to, values are what it forwards to on the PLC
PROXY_PORT_MAP = {
    34818: 44818,   # Proxy EtherNet/IP -> PLC EtherNet/IP
    1502: 502,      # Proxy Modbus/TCP  -> PLC Modbus/TCP
}

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

# Protocol names for logging (covers both proxy and real ports)
PORT_PROTOCOL_MAP = {
    34818: 'EtherNet/IP',
    44818: 'EtherNet/IP',
    1502: 'Modbus/TCP',
    502: 'Modbus/TCP',
}
