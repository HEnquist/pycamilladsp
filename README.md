# pycamilladsp
Python library for handling the communication with CamillaDSP via a websocket.

Install with 
```sh
pip install .
```

Included examples:

play_wav: Play a wav file. This example reads a configuration from a file, updates the capture device fto point at a given .wav file, and sends this modified config to CamillaDSP.
Usage example:
```sh
python play_wav.py 1234 /path/to/wavtest.yml /path/to/music.wav
```
