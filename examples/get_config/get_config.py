# get config
from camilladsp import CamillaConnection
import sys
import time

try:
    port = int(sys.argv[1])
except:
    print("Usage: Start CamillaDSP with the websocket server enabled:")
    print("> camilladsp -p4321 yourconfig.yml")
    print("Then run this script to print some parameters from the active config.")
    print("> python get_config.py 4321")
    sys.exit()

cdsp = CamillaConnection("127.0.0.1", port)
cdsp.connect()

conf = cdsp.get_config()

# Get some single parameters
print(f'Capture device type: {conf["devices"]["capture"]["type"]}')
print(f'Sample rate: {conf["devices"]["samplerate"]}')
print(f'Resampling enabled: {conf["devices"]["enable_resampling"]}')

# Print the whole playback and capture devices
print(f'Capture device: {str(conf["devices"]["capture"])}')
print(f'Playback device: {str(conf["devices"]["playback"])}')
