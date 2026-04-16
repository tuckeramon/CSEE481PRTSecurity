import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SSH_HOST = os.getenv("SSH_HOST", "192.168.1.222")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "pi")
LOCAL_BIND_PORT = int(os.getenv("SSH_LOCAL_BIND_PORT", "3307"))
REMOTE_MYSQL_PORT = int(os.getenv("REMOTE_MYSQL_PORT", "3306"))


class SSHTunnelManager:
    def __init__(self):
        self._tunnel = None
        self._status_callback = None
        self.local_port = LOCAL_BIND_PORT

    def set_callback(self, callback):
        """Set a status callback: callback(message: str, status: str)."""
        self._status_callback = callback

    def _emit(self, message, status="CONNECTING"):
        print(f"[SSH] {message}")
        if self._status_callback:
            self._status_callback(message, status)

    def start(self):
        """Open the SSH tunnel. Returns True on success. Blocks until connected."""
        try:
            from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
        except ImportError:
            self._emit("sshtunnel not installed — run: pip install sshtunnel paramiko", "FAILED")
            return False

        self._emit(f"Connecting to {SSH_USER}@{SSH_HOST}:{SSH_PORT} ...")

        candidates = [
            Path.home() / ".ssh" / "id_rsa",
            Path.home() / ".ssh" / "id_ed25519",
            Path.home() / ".ssh" / "id_ecdsa",
            Path.home() / ".ssh" / "id_dsa",
        ]
        ssh_key = next((str(p) for p in candidates if p.exists()), None)

        if ssh_key:
            self._emit(f"Using key: {Path(ssh_key).name}")
        else:
            self._emit("No key found in ~/.ssh/ — trying SSH agent", "WARNING")

        try:
            kwargs = dict(
                ssh_address_or_host=(SSH_HOST, SSH_PORT),
                ssh_username=SSH_USER,
                remote_bind_address=("127.0.0.1", REMOTE_MYSQL_PORT),
                local_bind_address=("127.0.0.1", LOCAL_BIND_PORT),
            )
            if ssh_key:
                kwargs["ssh_pkey"] = ssh_key

            self._emit("Opening tunnel ...")
            self._tunnel = SSHTunnelForwarder(**kwargs)
            self._tunnel.start()
            self.local_port = self._tunnel.local_bind_port

            # Let db.py pick up the tunneled port automatically
            os.environ["MYSQL_HOST"] = "127.0.0.1"
            os.environ["MYSQL_PORT"] = str(self.local_port)

            self._emit(
                f"Tunnel active  127.0.0.1:{self.local_port} → {SSH_HOST}:{REMOTE_MYSQL_PORT}",
                "CONNECTED",
            )
            return True

        except BaseSSHTunnelForwarderError as exc:
            self._emit(f"Tunnel failed: {exc}", "FAILED")
            self._tunnel = None
            return False
        except Exception as exc:
            self._emit(f"Unexpected error: {exc}", "FAILED")
            self._tunnel = None
            return False

    def stop(self):
        """Close the SSH tunnel if active."""
        if self._tunnel is not None:
            try:
                if self._tunnel.is_active:
                    self._tunnel.stop()
                    self._emit("SSH tunnel closed.", "DISCONNECTED")
            except Exception:
                pass
            self._tunnel = None

    @property
    def is_active(self):
        return self._tunnel is not None and self._tunnel.is_active
