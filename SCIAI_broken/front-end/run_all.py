"""
Frontend launcher script

MAJOR CHANGE: Removed log_server.py startup

OLD BEHAVIOR:
- Started TWO processes: log_server.py (Flask on port 5000) and run_gui.py
- log_server.py received HTTP POST requests from backend and wrote to cart_logs
- Required HTTP layer (WebRequester classes) to communicate between processes

NEW BEHAVIOR:
- Starts ONLY run_gui.py (the GUI application)
- No log_server.py needed - backend now writes directly to cart_logs table via SQL
- Simpler architecture: 2 processes instead of 3 (backend + frontend, no HTTP server)

Files Deleted:
- log_server.py (Flask HTTP server)
- WebRequester.py (HTTP client classes)
- WebRequesterConfig.py (HTTP configuration)
- WebRequester_test.py (HTTP tests)

Benefits:
- Eliminated HTTP overhead (~15-30ms latency per log)
- No port 5000 conflicts or firewall issues
- cart_logs now populates automatically from backend PLC events
- Simpler deployment and debugging
"""
import subprocess
import sys
import os

# Helper to get the python executable
PYTHON = sys.executable

# CHANGE: Only start GUI - log_server.py removed
# Backend (main.py) now logs directly to prt_unified database via PRTDB.log_to_cart_logs()
gui = subprocess.Popen([PYTHON, "run_gui.py"], cwd=os.path.dirname(__file__))

try:
    # Wait for GUI process to finish
    gui.wait()
except KeyboardInterrupt:
    print("Shutting down...")
    gui.terminate()
