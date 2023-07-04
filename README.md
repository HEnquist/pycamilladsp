![pyCamillaDSP](https://github.com/HEnquist/pycamilladsp/workflows/pyCamillaDSP/badge.svg)

# pyCamillaDSP
Companion Python library for CamillaDSP.
Works with CamillaDSP version 2.0.0 and up.

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
## Code quality
This library uses the following tools to ensure code quality:
- pylint
- mypy
- black
- pytest

Set up the development environment in conda:

```console
conda install pytest pylint black mypy
mypy --install-types
```

Run the entire suite of checks and tests:
```console
pylint camilladsp
mypy camilladsp 
black camilladsp
pytest
```

## Documentation
The documentation is generated by mkdocs and mkdocstrings.
It is generated from the templates stored in `docs`.
The content is autogenerated from the docstrings in the code.

Set up a conda environment:
```console
conda install mkdocs
pip install mkdocs-material
pip install mkdocstrings
```

Preview the documentation:

```console
mkdocs serve
````

Publish to Github pages:
```console
mkdocs gh-deploy
```