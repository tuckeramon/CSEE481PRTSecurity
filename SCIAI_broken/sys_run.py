import subprocess
import sys
import os

PYTHON = sys.executable

front_end = subprocess.Popen([PYTHON, "front-end/run_all.py"], cwd=os.path.dirname(__file__))
back_end = subprocess.Popen([PYTHON, "back-end/main.py"], cwd=os.path.dirname(__file__))

try:
    front_end.wait()
    back_end.wait()
except KeyboardInterrupt:
    print("Shutting down back-end and front-end...")
    front_end.terminate()
    back_end.terminate()