# pyCamillaDSP
Companion Python library for CamillaDSP.
Works with CamillaDSP version 0.3.2 and up.

Install with 
```sh
pip install .
```

## Plotting a configuration
This library provides the console command `plotcamillaconf`. Once the library is installed, the command should be available in your terminal.
To use it type:
```sh
plotcamillaconf /path/to/some/config.yml
```

This will plot the frequency response of all the defined filters, and show a block diagram of the pipeline.


## Communicating with the CamillaDSP process
This library provides an easy way to communicate with CamillaDSP via a websocket.

Simple example to connect to CamillaDSP to read the version (assuming CamillaDSP is running on the same machine and listening on port 1234):
```python
from camilladsp import CamillaConnection

cdsp = CamillaConnection("127.0.0.1", 1234)
cdsp.connect()
print("Version: {}".format(cdsp.get_version()))
```

### Classes
All communication functionality is provided by the class CamillaConnection. The contructor accepts two arguments: host and port.
```
CamillaConnection(host, port)
```

## Methods

The CamillaConnection class provides the following methods:

| Method   |  Description  |
|----------|---------------|
|`connect()` | Connect to the Websocket server. Must be called before any other method can be used.|
|`disconnect()` | Close the connection to the websocket.|
|`is_connected()` | Is websocket connected? Returns True or False.|
|`get_version()` | Read CamillaDSP version, returns a tuple with 3 elements|
|`get_state()` | Get current processing state. Returns one of "RUNNING", "PAUSED" or "INACTIVE".|
|`get_signal_range()` | Get current signal range.|
|`get_signal_range_dB()` | Get current signal range in dB.|
|`get_capture_rate_raw()` | Get current capture rate, raw value.|
|`get_capture_rate()` | Get current capture rate. Returns the nearest common value.|
|`get_update_interval()` | Get current update interval in ms.|
|`set_update_interval(value)` | Set current update interval in ms.|
|`get_rate_adjust()` | Get current value for rate adjust.|
|`stop()` | Stop processing and wait for new config if wait mode is active, else exit. |
|`exit()` | Stop processing and exit.|
|`reload()` | Reload config from disk.|
|`get_config_name()` | Get path to current config file.|
|`set_config_name(value)` | Set path to config file.|
|`get_config_raw()` | Get the active configuation in yaml format as a string.|
|`set_config_raw(value)` | Upload a new configuation in yaml format as a string.|
|`get_config()` | Get the active configuation as an object.|
|`set_config(config)` | Upload a new configuation from an object.|


## Evaluating filters
To plot the frequency response of a filter, use the function `plot_filter`. This is mostly meant for internal use by the `plotcamillaconf` command.
```python
plot_filter(filterconf, name=None, samplerate=44100, npoints=1000, toimage=False)
```
This will plot using PyPlot. The filter configuration `fiterconf` must be provided. The `samplerate` defaults to 44100 if not given. The filter `name` is used for labels. The number of points in the plot is set with `npoints`. If `toimage` is set to True, then it will instead return the plot as an svg image.

## Plotting the pipeline
To plot a block diagram of the pipeline, use the function `plot_pipeline`. This is mostly meant for internal use by the `plotcamillaconf` command.
```python
plot_pipeline(conf, toimage=False)
```
This takes a full CamillaDSP configuration, `conf`. It will then plot the pipeline using PyPlot. If `toimage` is set to True, then it will instead return the plot as an svg image.

# Included examples:

play_wav: Play a wav file. This example reads a configuration from a file, updates the capture device fto point at a given .wav file, and sends this modified config to CamillaDSP.
Usage example:
```sh
python play_wav.py 1234 /path/to/wavtest.yml /path/to/music.wav
```
