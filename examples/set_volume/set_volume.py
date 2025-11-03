# set volume
from camilladsp import CamillaClient
import sys
import time

try:
    port = int(sys.argv[1])
    new_vol = float(sys.argv[2])
except:
    print(
        "Usage: Make sure that your pipeline includes Volume filters for each channel."
    )
    print("Then start CamillaDSP with the websocket server enabled:")
    print("> camilladsp -p4321 yourconfig.yml")
    print("Then set the volume")
    print("> python set_volume.py 4321 -12.3")
    sys.exit()

cdsp = CamillaClient("127.0.0.1", port)
cdsp.connect()

current_vol = cdsp.volume.main()
print(f"Current volume: {current_vol} dB")
print(f"Changing volume to: {new_vol} dB")
cdsp.volume.set_main(new_vol)
