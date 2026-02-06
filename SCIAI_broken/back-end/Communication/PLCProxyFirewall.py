"""
Application-Layer Whitelist Proxy Firewall for PLC Protection

Sits between the network and the PLC, only forwarding traffic from
whitelisted IP addresses. All blocked traffic is logged to PLCSecurityLogs
for correlation by the CorrelationEngine.

ARCHITECTURE:
    External hosts -> PLCProxyFirewall (listens on alternate proxy ports)
                      |-- whitelist check
                      |-- ALLOW -> forward to real PLC port
                      |-- DENY  -> log + close connection
    Backend app    -> connects directly to PLC (trusted, bypasses proxy)

PORT MAPPING:
    Proxy port 34818  ->  PLC port 44818 (EtherNet/IP)
    Proxy port 1502   ->  PLC port 502   (Modbus/TCP)

INTEGRATION:
    - Logs to PLCSecurityLogs via PRTDB.log_plc_security_event()
    - Uses EVENT_FIREWALL_BLOCK and EVENT_FIREWALL_ALLOW event types
    - CorrelationEngine detects repeated blocks via CORR_004 rule

THREADING MODEL:
    - One daemon listener thread per proxied port
    - One daemon relay thread per accepted whitelisted connection
    - All threads are daemon threads and terminate with the main process
"""

import socket
import threading
import select

from Communication.FirewallConfig import PORT_PROTOCOL_MAP, LOG_ALLOWED_CONNECTIONS


class PLCProxyFirewall:
    """
    TCP proxy firewall that whitelists IP addresses for PLC access.

    Follows the same pattern as PLCSecurityMonitor:
    - Instantiated with prt_unified for logging
    - Started from main.py
    - Logs security events to PLCSecurityLogs table
    """

    BUFFER_SIZE = 4096
    RELAY_TIMEOUT = 30.0
    SELECT_TIMEOUT = 1.0

    def __init__(self, prtdb, plc_target_ip, proxy_port_map, proxy_bind_ip='0.0.0.0', whitelist_ips=None):
        """
        Initialize the proxy firewall.

        :param prtdb: PRTDB instance for security logging
        :param plc_target_ip: Real PLC IP to forward traffic to
        :param proxy_port_map: Dict mapping proxy listen port -> real PLC target port
                               e.g., {34818: 44818, 1502: 502}
        :param proxy_bind_ip: IP to bind proxy listeners on
        :param whitelist_ips: Initial set of whitelisted IP addresses
        """
        self.prtdb = prtdb
        self.plc_target_ip = plc_target_ip
        self.proxy_port_map = proxy_port_map
        self.proxy_bind_ip = proxy_bind_ip

        # Static whitelist from config
        self._static_whitelist = set(whitelist_ips) if whitelist_ips else set()
        self._static_whitelist.add('127.0.0.1')  # Always allow localhost

        # Merged whitelist (static + DB) - replaced atomically by refresh_whitelist()
        self._whitelist = set(self._static_whitelist)

        # Load dynamic entries from DB on init
        self._load_whitelist_from_db()

        # State
        self._running = False
        self._listener_sockets = {}   # proxy_port -> socket
        self._listener_threads = {}   # proxy_port -> thread

        # Stats (protected by lock for thread-safe updates)
        self._stats_lock = threading.Lock()
        self._allowed_count = 0
        self._blocked_count = 0
        self._active_connections = 0

    def _load_whitelist_from_db(self):
        """Load whitelisted IPs from PLCFirewallWhitelist table and merge with static config."""
        try:
            entries = self.prtdb.get_firewall_whitelist()
            db_ips = {row['ip_address'] for row in entries}
            self._whitelist = self._static_whitelist | db_ips
        except Exception as e:
            print(f"FIREWALL: Warning - could not load whitelist from DB: {e}")
            self._whitelist = set(self._static_whitelist)

    def refresh_whitelist(self):
        """
        Reload whitelist from config + database.
        Called periodically from main loop. The set replacement is atomic
        due to Python's GIL, so reader threads see a consistent snapshot.
        """
        self._load_whitelist_from_db()

    def is_whitelisted(self, ip_address):
        """
        Check if an IP address is in the whitelist.

        :param ip_address: IP to check
        :return: True if allowed, False if blocked
        """
        return ip_address in self._whitelist

    def _log_firewall_event(self, source_ip, dest_port, allowed, message, severity="INFO"):
        """
        Log a firewall event to PLCSecurityLogs via PRTDB.

        :param source_ip: Source IP of the connection attempt
        :param dest_port: Target port (the real PLC port, not the proxy port)
        :param allowed: Whether connection was allowed
        :param message: Human-readable description
        :param severity: Log severity level
        """
        event_type = self.prtdb.EVENT_FIREWALL_ALLOW if allowed else self.prtdb.EVENT_FIREWALL_BLOCK
        protocol = PORT_PROTOCOL_MAP.get(dest_port, f'port {dest_port}')

        self.prtdb.log_plc_security_event(
            plc_ip=source_ip,
            event_type=event_type,
            event_message=message,
            severity=severity,
            current_state="ALLOWED" if allowed else "BLOCKED",
            raw_data={
                "source_ip": source_ip,
                "dest_port": dest_port,
                "protocol": protocol,
                "action": "ALLOWED" if allowed else "BLOCKED"
            }
        )

    def start(self):
        """Start proxy listeners on all configured ports."""
        self._running = True

        for proxy_port, target_port in self.proxy_port_map.items():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(1.0)  # Allow periodic check of _running flag
                sock.bind((self.proxy_bind_ip, proxy_port))
                sock.listen(5)
                self._listener_sockets[proxy_port] = sock

                thread = threading.Thread(
                    target=self._listener_thread,
                    args=(proxy_port, target_port),
                    daemon=True,
                    name=f"firewall-listener-{proxy_port}"
                )
                thread.start()
                self._listener_threads[proxy_port] = thread

                protocol = PORT_PROTOCOL_MAP.get(proxy_port, f'port {proxy_port}')
                print(f"FIREWALL: Listening on {self.proxy_bind_ip}:{proxy_port} -> {self.plc_target_ip}:{target_port} ({protocol})")
            except Exception as e:
                print(f"FIREWALL: Failed to start listener on port {proxy_port}: {e}")

    def stop(self):
        """Stop all proxy listeners and close active relay connections."""
        self._running = False

        for port, sock in self._listener_sockets.items():
            try:
                sock.close()
            except Exception:
                pass

        for port, thread in self._listener_threads.items():
            thread.join(timeout=3.0)

        self._listener_sockets.clear()
        self._listener_threads.clear()
        print("FIREWALL: All listeners stopped")

    def _listener_thread(self, proxy_port, target_port):
        """
        Listener thread for a single proxied port.
        Accepts connections, checks whitelist, spawns relay threads or blocks.

        :param proxy_port: Port number the proxy is listening on
        :param target_port: Real PLC port to forward to
        """
        sock = self._listener_sockets[proxy_port]
        protocol = PORT_PROTOCOL_MAP.get(proxy_port, f'port {proxy_port}')

        while self._running:
            try:
                client_sock, addr = sock.accept()
                source_ip = addr[0]

                if self.is_whitelisted(source_ip):
                    # Allowed - spawn relay thread
                    with self._stats_lock:
                        self._allowed_count += 1

                    if LOG_ALLOWED_CONNECTIONS:
                        self._log_firewall_event(
                            source_ip=source_ip,
                            dest_port=target_port,
                            allowed=True,
                            message=f"Allowed {protocol} connection from {source_ip}",
                            severity="INFO"
                        )

                    relay = threading.Thread(
                        target=self._relay_thread,
                        args=(client_sock, self.plc_target_ip, target_port, source_ip),
                        daemon=True,
                        name=f"firewall-relay-{source_ip}-{proxy_port}"
                    )
                    relay.start()
                else:
                    # Blocked - log and close
                    with self._stats_lock:
                        self._blocked_count += 1

                    self._log_firewall_event(
                        source_ip=source_ip,
                        dest_port=target_port,
                        allowed=False,
                        message=f"BLOCKED {protocol} connection from {source_ip} (not whitelisted)",
                        severity="WARNING"
                    )

                    try:
                        client_sock.close()
                    except Exception:
                        pass

            except socket.timeout:
                continue  # Normal - just check _running flag and loop
            except OSError:
                if self._running:
                    print(f"FIREWALL: Listener socket error on port {proxy_port}")
                break  # Socket was closed (during stop())

    def _relay_thread(self, client_sock, target_ip, target_port, source_ip):
        """
        Bidirectional TCP relay between client and PLC.
        Uses select() for non-blocking relay.

        :param client_sock: Accepted client socket
        :param target_ip: Real PLC IP
        :param target_port: Real PLC port
        :param source_ip: Client's IP address (for logging)
        """
        plc_sock = None

        with self._stats_lock:
            self._active_connections += 1

        try:
            # Connect to real PLC
            plc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            plc_sock.settimeout(self.RELAY_TIMEOUT)
            plc_sock.connect((target_ip, target_port))

            # Bidirectional relay
            sockets = [client_sock, plc_sock]
            while self._running:
                readable, _, errored = select.select(sockets, [], sockets, self.SELECT_TIMEOUT)

                if errored:
                    break

                for sock in readable:
                    try:
                        data = sock.recv(self.BUFFER_SIZE)
                        if not data:
                            # Connection closed
                            return
                        # Forward to the other socket
                        if sock is client_sock:
                            plc_sock.sendall(data)
                        else:
                            client_sock.sendall(data)
                    except Exception:
                        return

        except Exception as e:
            protocol = PORT_PROTOCOL_MAP.get(target_port, f'port {target_port}')
            print(f"FIREWALL: Relay error for {source_ip} -> {target_ip}:{target_port} ({protocol}): {e}")
        finally:
            with self._stats_lock:
                self._active_connections -= 1

            for sock in [client_sock, plc_sock]:
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass

    def get_stats(self):
        """
        Return firewall statistics.

        :return: Dict with allowed_count, blocked_count, active_connections, whitelist_size
        """
        with self._stats_lock:
            return {
                "allowed_count": self._allowed_count,
                "blocked_count": self._blocked_count,
                "active_connections": self._active_connections,
                "whitelist_size": len(self._whitelist),
                "listening_ports": list(self._listener_sockets.keys())
            }
