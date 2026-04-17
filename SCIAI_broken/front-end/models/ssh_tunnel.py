import os
import socket
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

SSH_HOST = os.getenv("SSH_HOST", "192.168.1.222")
SSH_PORT = int(os.getenv("SSH_PORT", "22"))
SSH_USER = os.getenv("SSH_USER", "edadmin")

_CONNECT_TIMEOUT = 15  # seconds to wait for SSH to become reachable


class SSHTunnelManager:
    def __init__(self):
        self._proc = None
        self._status_callback = None

    def set_callback(self, callback):
        """callback(message: str, status: str)"""
        self._status_callback = callback

    def _emit(self, message, status="CONNECTING"):
        print(f"[SSH] {message}")
        if self._status_callback:
            self._status_callback(message, status)

    def start(self):
        """Open a persistent SSH connection to the Pi. Returns True on success."""
        self._emit(f"Connecting to {SSH_USER}@{SSH_HOST}:{SSH_PORT} ...")

        cmd = [
            "ssh",
            "-N",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=10",
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-p", str(SSH_PORT),
            f"{SSH_USER}@{SSH_HOST}",
        ]

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

        # Wait until SSH port on the Pi is reachable (connection established)
        self._emit(f"Waiting for SSH handshake ...")
        deadline = time.time() + _CONNECT_TIMEOUT
        while time.time() < deadline:
            if self._proc.poll() is not None:
                stderr = self._proc.stderr.read().decode(errors="replace").strip()
                self._emit(f"SSH failed: {stderr or 'no error output'}", "FAILED")
                self._proc = None
                return False

            try:
                with socket.create_connection((SSH_HOST, SSH_PORT), timeout=2):
                    # Give ssh a moment to complete the handshake after TCP connects
                    time.sleep(1)
                    break
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
        else:
            self._emit(f"Timed out after {_CONNECT_TIMEOUT}s — is {SSH_HOST} reachable?", "FAILED")
            self._proc.terminate()
            self._proc = None
            return False

        # Confirm the process is still running after handshake
        if self._proc.poll() is not None:
            stderr = self._proc.stderr.read().decode(errors="replace").strip()
            self._emit(f"SSH failed: {stderr or 'authentication error'}", "FAILED")
            self._proc = None
            return False

        self._emit(f"Connected to {SSH_USER}@{SSH_HOST}", "CONNECTED")
        return True

    def stop(self):
        if self._proc is not None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                pass
            self._proc = None
            self._emit("SSH connection closed.", "DISCONNECTED")

    def run_command(self, remote_cmd, sudo=False):
        """Run a command on the Pi over a new SSH connection.

        Returns (stdout, stderr, returncode).  Blocks until the command exits.
        Pass sudo=True to prepend ``sudo`` — requires NOPASSWD in sudoers for
        the relevant commands so no password prompt is issued.
        """
        full_cmd = f"sudo {remote_cmd}" if sudo else remote_cmd
        stdin_data = None

        ssh_cmd = [
            "ssh",
            "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-o", "ConnectTimeout=10",
            "-p", str(SSH_PORT),
            f"{SSH_USER}@{SSH_HOST}",
            full_cmd,
        ]

        try:
            result = subprocess.run(
                ssh_cmd,
                input=stdin_data,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            stdout = result.stdout.decode(errors="replace").strip()
            stderr = result.stderr.decode(errors="replace").strip()
            return stdout, stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out after 60 s", 1
        except Exception as exc:
            return "", str(exc), 1

    @property
    def is_active(self):
        return self._proc is not None and self._proc.poll() is None
