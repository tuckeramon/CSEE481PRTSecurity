import os
import socket
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

SSH_HOST = os.getenv("SSH_HOST", "192.168.1.222")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "pi")
LOCAL_BIND_PORT = int(os.getenv("SSH_LOCAL_BIND_PORT", "3307"))
REMOTE_MYSQL_PORT = int(os.getenv("REMOTE_MYSQL_PORT", "3306"))

_TUNNEL_TIMEOUT = 15  # seconds to wait for port to open


class SSHTunnelManager:
    def __init__(self):
        self._proc = None
        self._status_callback = None
        self.local_port = LOCAL_BIND_PORT

    def set_callback(self, callback):
        """callback(message: str, status: str)"""
        self._status_callback = callback

    def _emit(self, message, status="CONNECTING"):
        print(f"[SSH] {message}")
        if self._status_callback:
            self._status_callback(message, status)

    def start(self):
        """Start the SSH tunnel via the system ssh binary. Returns True on success."""
        self._emit(f"Connecting to {SSH_USER}@{SSH_HOST}:{SSH_PORT} ...")

        cmd = [
            "ssh",
            "-N",
            "-L", f"{LOCAL_BIND_PORT}:127.0.0.1:{REMOTE_MYSQL_PORT}",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", f"ConnectTimeout=10",
            "-p", str(SSH_PORT),
            f"{SSH_USER}@{SSH_HOST}",
        ]
        self._emit(f"ssh -N -L {LOCAL_BIND_PORT}:127.0.0.1:{REMOTE_MYSQL_PORT} {SSH_USER}@{SSH_HOST}")

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
        except FileNotFoundError:
            self._emit("'ssh' not found — install OpenSSH for Windows", "FAILED")
            return False

        # Poll the local port until SSH binds it (tunnel ready) or the process exits
        self._emit(f"Waiting for local port {LOCAL_BIND_PORT} to open ...")
        deadline = time.time() + _TUNNEL_TIMEOUT
        while time.time() < deadline:
            # Check if ssh exited early (auth failure, host unreachable, etc.)
            if self._proc.poll() is not None:
                stderr = self._proc.stderr.read().decode(errors="replace").strip()
                self._emit(f"SSH process exited: {stderr or 'no error output'}", "FAILED")
                self._proc = None
                return False

            try:
                with socket.create_connection(("127.0.0.1", LOCAL_BIND_PORT), timeout=1):
                    break
            except (ConnectionRefusedError, OSError):
                time.sleep(0.4)
        else:
            self._emit(f"Timed out after {_TUNNEL_TIMEOUT}s — host unreachable?", "FAILED")
            self._proc.terminate()
            self._proc = None
            return False

        self.local_port = LOCAL_BIND_PORT
        os.environ["MYSQL_HOST"] = "127.0.0.1"
        os.environ["MYSQL_PORT"] = str(self.local_port)

        self._emit(
            f"Tunnel active  127.0.0.1:{self.local_port} → {SSH_HOST}:{REMOTE_MYSQL_PORT}",
            "CONNECTED",
        )
        return True

    def stop(self):
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                pass
            self._proc = None
            self._emit("SSH tunnel closed.", "DISCONNECTED")

    @property
    def is_active(self):
        return self._proc is not None and self._proc.poll() is None
