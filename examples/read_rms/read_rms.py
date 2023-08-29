# read rms
from camilladsp import CamillaClient
import sys
import time

try:
    port = int(sys.argv[1])
except:
    print("Usage: start CamillaDSP with the socketserver enabled:")
    print("> camilladsp -p4321 yourconfig.yml")
    print("Then read the signal level")
    print("> python read_rms.py 4321")
    sys.exit()

cdsp = CamillaClient("127.0.0.1", port)
cdsp.connect()

print("Reading playback signal RMS, press Ctrl+c to stop")
while True:
    print(cdsp.levels.playback_rms())
    time.sleep(1)
