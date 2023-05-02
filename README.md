![pyCamillaDSP](https://github.com/HEnquist/pycamilladsp/workflows/pyCamillaDSP/badge.svg)

# pyCamillaDSP
Companion Python library for CamillaDSP.
Works with CamillaDSP version 2.0.0 and up.

Download the library, either by `git clone` or by downloading a zip file of the code. Then unpack the files, go to the folder containing the `setup.py` file and run: 
```sh
pip install .
```
TODO smarter command with pip git
Note that on some systems the command is `pip3` instead of `pip`.

## Dependencies
pyCamillaDSP requires python 3.6 or newer and the package websocket-client.

These are the names of the packages needed:

| Distribution    | python  | websocket-client         |
|-----------------|---------|--------------------------|
| Fedora          | python3 | python3-websocket-client |
| Debian/Raspbian | python3 | python3-websocket        |
| Arch            | python  | python-websocket-client  |
| pip             | -       | websocket_client         |
| Anaconda        | -       | websocket_client         |

### Linux
TODO add something about new pip --break-system-thing
Most linux distributions have Python 3.6 or newer installed by default. Use the normal package manager to install the packages.

### Windows
Use Anaconda: https://www.anaconda.com/products/individual. Then use Anaconda Navigator to install `websocket_client`.

### macOS
On macOS use either Anaconda or Homebrew. The Anaconda procedure is the same as for Windows. 

For Homebrew, install Python with `brew install python`, after which you can install the needed packages with pip, `pip3 install websocket_client`.

## Communicating with the CamillaDSP process
This library provides an easy way to communicate with CamillaDSP via a websocket.

Simple example to connect to CamillaDSP to read the version (assuming CamillaDSP is running on the same machine and listening on port 1234):
```python
from camilladsp import CamillaClient

cdsp = CamillaClient("127.0.0.1", 1234)
cdsp.connect()
print("Version: {}".format(cdsp.versions.camilladsp()))
```

See the [published documentation](https://henquist.github.io/pycamilladsp/)for descriptions of all classes and methods.

# Included examples:

## read_rms
Read the playback signal level continuously and print in the terminal, until stopped by Ctrl+c. 
```sh
python read_rms.py 1234
```

## get_config
Read the configuration and print some parameters. 
```sh
python get_config.py 1234
```

## set_volume
Set the volume control to a new value. First argument is websocket port, second is new volume in dB.
For this to work, CamillaDSP must be running a configuration that has Volume filters in the pipeline for every channel.
```sh
python set_volume.py 1234 -12.3
```

## play_wav
Play a wav file. This example reads a configuration from a file, updates the capture device fto point at a given .wav file, and sends this modified config to CamillaDSP.
Usage example:
```sh
python play_wav.py 1234 /path/to/wavtest.yml /path/to/music.wav
```

# Development info
TODO clean up here
quality:
pylint camilladsp
mypy camilladsp 
black camilladsp
pytest

deps:
conda install pytest pylint black mypy
mypy --install-types

conda install mkdocs
pip install mkdocs-material
pip install mkdocstrings

preview: mkdocs serve
deploy: mkdocs gh-deploy