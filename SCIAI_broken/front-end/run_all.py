import subprocess
import sys
import os

# Helper to get the python executable
PYTHON = sys.executable

# Start log_server.py
log_server = subprocess.Popen([PYTHON, "log_server.py"], cwd=os.path.dirname(__file__))

# Start run_gui.py
gui = subprocess.Popen([PYTHON, "run_gui.py"], cwd=os.path.dirname(__file__))

try:
    # Wait for both processes to finish (they likely won't unless you close them)
    log_server.wait()
    gui.wait()
except KeyboardInterrupt:
    print("Shutting down...")
    log_server.terminate()
    gui.terminate()
