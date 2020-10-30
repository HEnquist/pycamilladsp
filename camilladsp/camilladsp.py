import yaml
import json
from websocket import create_connection
import math
from threading import Lock

VERSION = (0, 4, 1)

STANDARD_RATES = [
    8000,
    11025,
    16000,
    22050,
    32000,
    44100,
    48000,
    88200,
    96000,
    176400,
    192000,
    352800,
    384000,
]


class CamillaError(ValueError):
    """
    A class representing errors returned by CamillaDSP
    """

    pass


class CamillaConnection:
    """
    Class for communicating with CamillaDSP.
    """

    def __init__(self, host, port):
        """
        Connect to CamillaDSP on the specified host and port.
        """
        self._host = host
        self._port = int(port)
        self._ws = None
        self._version = None
        self._lock = Lock()

    def _query(self, command, arg=None):
        if self._ws is not None:
            if arg:
                query = json.dumps({command: arg})
            else:
                query = json.dumps(command)
            try:
                with self._lock:
                    self._ws.send(query)
                    rawrepl = self._ws.recv()
            except Exception as _e:
                self._ws = None
                raise IOError("Lost connection to CamillaDSP")
            return self._handle_reply(command, rawrepl)
        else:
            raise IOError("Not connected to CamillaDSP")

    def _handle_reply(self, command, rawreply):
        try:
            reply = json.loads(rawreply)
            value = None
            if command in reply:
                state = reply[command]["result"]
                if "value" in reply[command]:
                    value = reply[command]["value"]
                if state == "Error" and value is not None:
                    raise CamillaError(value)
                elif state == "Error" and value is None:
                    raise CamillaError("Command returned an error")
                elif state == "Ok" and value is not None:
                    return value
                return
            else:
                raise IOError("Invalid response received: {}".format(rawreply))
        except json.JSONDecodeError:
            raise IOError("Invalid response received: {}".format(rawreply))

    def _update_version(self, resp):
        self._version = tuple(resp.split(".", 3))

    def connect(self):
        """
        Connect to the websocket of CamillaDSP.
        """
        try:
            with self._lock:
                self._ws = create_connection(
                    "ws://{}:{}".format(self._host, self._port)
                )
            rawvers = self._query("GetVersion")
            self._update_version(rawvers)
        except Exception as _e:
            self._ws = None
            raise

    def disconnect(self):
        """
        Close the connection to the websocket.
        """
        if self._ws is not None:
            try:
                with self._lock:
                    self._ws.close()
            except Exception as _e:
                pass
            self._ws = None

    def is_connected(self):
        """
        Is websocket connected? Returns True or False.
        """
        return self._ws is not None

    def get_version(self):
        """Read CamillaDSP version, returns a tuple of (major, minor, patch)."""
        return self._version

    def get_library_version(self):
        """Read pycamilladsp version, returns a tuple of (major, minor, patch)."""
        return VERSION

    def get_state(self):
        """
        Get current processing state.
        """
        state = self._query("GetState")
        return state

    def get_signal_range(self):
        """
        Get current signal range. Maximum value is 2.0.
        """
        sigrange = self._query("GetSignalRange")
        return float(sigrange)

    def get_signal_range_dB(self):
        """
        Get current signal range in dB. Full scale is 0 dB.
        """
        sigrange = self.get_signal_range()
        if sigrange > 0.0:
            range_dB = 20.0 * math.log10(sigrange / 2.0)
        else:
            range_dB = -1000
        return range_dB

    def get_capture_rate_raw(self):
        """
        Get current capture rate, raw value.
        """
        rate = self._query("GetCaptureRate")
        return int(rate)

    def get_capture_rate(self):
        """
        Get current capture rate. Returns the nearest common value.
        """
        rate = self.get_capture_rate_raw()
        if 0.9 * STANDARD_RATES[0] < rate < 1.1 * STANDARD_RATES[-1]:
            return min(STANDARD_RATES, key=lambda val: abs(val - rate))
        else:
            return None

    def get_update_interval(self):
        """
        Get current update interval in ms.
        """
        interval = self._query("GetUpdateInterval")
        return int(interval)

    def set_update_interval(self, value):
        """
        Set current update interval in ms.
        """
        self._query("SetUpdateInterval", arg=value)

    def get_rate_adjust(self):
        """
        Get current value for rate adjust, 1.0 means 1:1 resampling.
        """
        adj = self._query("GetRateAdjust")
        return float(adj)

    def get_buffer_level(self):
        """
        Get current buffer level of the playback device.
        """
        level = self._query("GetBufferLevel")
        return int(level)

    def get_clipped_samples(self):
        """
        Get number of clipped samples since the config was loaded.
        """
        clipped = self._query("GetClippedSamples")
        return int(clipped)

    def stop(self):
        """
        Stop processing and wait for new config if wait mode is active, else exit.
        """
        self._query("Stop")

    def exit(self):
        """
        Stop processing and exit.
        """
        self._query("Exit")

    def reload(self):
        """
        Reload config from disk.
        """
        self._query("Reload")

    def get_config_name(self):
        """
        Get path to current config file.
        """
        name = self._query("GetConfigName")
        return name

    def set_config_name(self, value):
        """
        Set path to config file.
        """
        self._query("SetConfigName", arg=value)

    def get_config_raw(self):
        """
        Get the active configuation in yaml format as a string.
        """
        config_string = self._query("GetConfig")
        return config_string

    def set_config_raw(self, config_string):
        """
        Upload a new configuation in yaml format as a string.
        """
        self._query("SetConfig", arg=config_string)

    def get_config(self):
        """
        Get the active configuation as a Python object.
        """
        config_string = self.get_config_raw()
        config_object = yaml.safe_load(config_string)
        return config_object

    def read_config(self, config_string):
        """
        Read a config from yaml string and return the contents 
        as a Python object, with defaults filled out with their default values.
        """
        config_raw = self._query("ReadConfig", arg=config_string)
        config_object = yaml.safe_load(config_raw)
        return config_object

    def read_config_file(self, filename):
        """
        Read a config file from disk and return the contents as a Python object.
        """
        config_raw = self._query("ReadConfigFile", arg=filename)
        config = yaml.safe_load(config_raw)
        return config

    def set_config(self, config_object):
        """
        Upload a new configuation from a Python object.
        """
        config_raw = yaml.dump(config_object)
        self.set_config_raw(config_raw)

    def validate_config(self, config_object):
        """
        Validate a configuration object.
        Returns the validated config with all optional fields filled with defaults.
        Raises a CamillaError on errors.
        """
        config_string = yaml.dump(config_object)
        validated_string = self._query("ValidateConfig", arg=config_string)
        validated_object = yaml.safe_load(validated_string)
        return validated_object


if __name__ == "__main__":  # pragma: no cover
    """Testing area"""
    print("\n---Connect---")
    cdsp = CamillaConnection("127.0.0.1", 1234)
    cdsp.connect()

    print("\n---Read parameters---")
    print("Version: {}".format(cdsp.get_version()))
    print("State: {}".format(cdsp.get_state()))
    print("ValueRange: {}".format(cdsp.get_signal_range()))
    print("ValueRange dB: {}".format(cdsp.get_signal_range_dB()))
    print("CaptureRate raw: {}".format(cdsp.get_capture_rate_raw()))
    print("CaptureRate: {}".format(cdsp.get_capture_rate()))
    print("RateAdjust: {}".format(cdsp.get_rate_adjust()))

    print("\n---SetUpdateInterval 500---")
    cdsp.set_update_interval(500)
    print("UpdateInterval: {}".format(cdsp.get_update_interval()))

    print("\n---SetUpdateInterval invalid value---")
    try:
        cdsp.set_update_interval(-500)
    except Exception as e:
        print("Reply:", e)

    print("\n---ReadConfigFile---")
    conf = cdsp.read_config_file(
        "/home/henrik/rustfir/rustfir/exampleconfigs/simpleconfig.yml"
    )
    print(conf)

    print("\n---ValidateConfig---")
    try:
        valconf = cdsp.validate_config(conf)
        print("ValidateConfig OK:", valconf)
    except CamillaError as e:
        print("ValidateConfig Error:", e)

    print("\n---ReadConfig---")
    readconf = cdsp.read_config(yaml.dump(conf))
    print(readconf)

    print("\n---ReadConfigFile non-existing---")
    try:
        conf = cdsp.read_config_file("/some/bad/path.yml")
    except Exception as e:
        print("ReadConfigFile Error:", e)

    print("\n---ValidateConfig broken config---")
    conf["devices"]["capture"]["type"] = "Teapot"
    try:
        valconf = cdsp.validate_config(conf)
        print("ValidateConfig OK:", valconf)
    except CamillaError as e:
        print("ValidateConfig Error:", e)
    
    #cdsp.disconnect()
