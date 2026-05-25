# subscribe to events
from camilladsp import CamillaClient
import sys
import threading
import time


def print_capture_levels(event):
    print(f"capture levels: {event}")
    return True


def print_state(event):
    print(f"state: {event}")
    return True


def subscribe_capture_levels(port):
    cdsp = CamillaClient("127.0.0.1", port)
    cdsp.connect()
    try:
        cdsp.levels.subscribe_signal_levels(print_capture_levels, side="capture")
    finally:
        cdsp.disconnect()


def subscribe_state(port):
    cdsp = CamillaClient("127.0.0.1", port)
    cdsp.connect()
    try:
        cdsp.general.subscribe_state(print_state)
    finally:
        cdsp.disconnect()


try:
    port = int(sys.argv[1])
except:
    print("Usage: start CamillaDSP with the socketserver enabled:")
    print("> camilladsp -p4321 yourconfig.yml")
    print("Then run this script to print capture signal levels and state events.")
    print("> python subscribe_events.py 4321")
    sys.exit()


level_thread = threading.Thread(
    target=subscribe_capture_levels, args=(port,), daemon=True
)
state_thread = threading.Thread(target=subscribe_state, args=(port,), daemon=True)

level_thread.start()
state_thread.start()

print("Listening for capture signal level and state events, press Ctrl+C to stop")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
