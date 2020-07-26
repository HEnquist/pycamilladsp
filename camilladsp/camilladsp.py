#play wav
import yaml
from websocket import create_connection
import math

standard_rates = [8000, 11025, 16000, 22050, 32000, 44100, 48000, 88200, 96000, 176400, 192000, 352800, 384000]

class CamillaDSP:
    '''Class for communicating with CamillaDSP'''

    def __init__(self, host, port):
        '''Connect to CamillaDSP on the specified host and port'''
        self._host = host
        self._port = int(port)
        self._ws = None
        self._version = None
    
    def connect(self):
        '''Connect to the websocket of CamillaDSP'''
        try:
            self._ws = create_connection("ws://{}:{}".format(self._host, self._port))
            rawvers = self._query("getversion")
            self._update_version(rawvers)
        except Exception as e:
            self._ws = None
            raise

    def _query(self, command):
        if self._ws is not None:
            try:
                self._ws.send(command)
                rawrepl = self._ws.recv()
                repl = self._parse_response(rawrepl)
                if repl[0] == command.lower():
                    if len(repl) > 1:
                        return repl[1]
                    return
                else:
                    raise IOError("Invalid response received") 
            except Exception as e:
                self._ws = None
                raise IOError("Lost connection to CamillaDSP")
        else:
            raise IOError("Not connected to CamillaDSP")

    def _set_value(self, command, value):
        if self._ws is not None:
            self._ws.send("{}:{}".format(command, value))
            rawrepl = self._ws.recv()
            repl = self._parse_response(rawrepl)
            if repl[0] == command.lower():
                return None
            else:
                raise IOError("Invalid response received") 
        else:
            raise IOError("Not connected")

    def _parse_response(self, resp):
        parts = resp.split(":",3)
        state = parts[0]
        command = parts[1]
        if state == "OK":
            if len(parts) > 2:
                return (command.lower(), parts[2])
            else:
                return (command.lower(),)
        else:
            raise ValueError("Command returned error")

    def _update_version(self, resp):
        self._version = tuple(resp.split(".", 3))

    def get_version(self):
        '''Read CamillaDSP version, returns a tuple.'''
        return self._version

    def get_state(self):
        '''Get current processing state.'''
        state = self._query("getstate")
        return state

    def get_signal_range(self):
        '''Get current signal range.'''
        sigrange = self._query("getsignalrange")
        return float(sigrange)

    def get_signal_range_dB(self):
        '''Get current signal range in dB.'''
        sigrange = self.get_signal_range()
        if sigrange > 0.0:
            range_dB = 20.0 * math.log10(sigrange/2.0)
        else:
            range_dB = -1000
        return range_dB

    def get_capture_rate_raw(self):
        '''Get current capture rate, raw value.'''
        rate = self._query("getcapturerate")
        return int(rate)

    def get_capture_rate(self):
        '''Get current capture rate. Returns the nearest common value.'''
        rate = self.get_capture_rate_raw()
        if 0.9*standard_rates[0] < rate < 1.1*standard_rates[-1]:
            return min(standard_rates, key=lambda val: abs(val - rate))
        else:
            return None

    def get_update_interval(self):
        '''Get current update interval in ms.'''
        interval = self._query("getupdateinterval")
        return int(interval)

    def set_update_interval(self, value):
        '''Set current update interval in ms.'''
        self._set_value("setupdateinterval", value)

    def get_rate_adjust(self):
        '''Get current value for rate adjust in %.'''
        adj = self._query("getrateadjust")
        return float(adj)

    def stop(self):
        '''Stop processing and wait for new config if wait mode is active, else exit. '''
        self._query("stop")

    def exit(self):
        '''Stop processing and exit.'''
        self._query("exit")

    def reload(self):
        '''Reload config from disk.'''
        self._query("reload")

    def get_config_name(self):
        '''Get path to current config file.'''
        name = self._query("getconfigname")
        return name

    def set_config_name(self, value):
        '''Set path to config file.'''
        self._set_value("setconfigname", value)

    def get_config_raw(self):
        '''Get the active configuation in yaml format as a string.'''
        config = self._query("getconfig")
        return config

    def set_config_raw(self, value):
        '''Upload a new configuation in yaml format as a string.'''
        self._set_value("setconfig", value)

    def get_config(self):
        '''Get the active configuation as an object'''
        config_raw = self.get_config_raw()
        config=yaml.safe_load(config_raw)
        return config

    def set_config(self, config):
        '''Upload a new configuation from an object'''
        config_raw = yaml.dump(config)
        self.set_config_raw(config_raw)


if __name__ == "__main__":
    cdsp = CamillaDSP("127.0.0.1", 1234)
    cdsp.connect()
    print("Version: {}".format(cdsp.get_version()))
    print("State: {}".format(cdsp.get_state()))
    print("ValueRange: {}".format(cdsp.get_signal_range()))
    print("ValueRange dB: {}".format(cdsp.get_signal_range_dB()))
    print("CaptureRate raw: {}".format(cdsp.get_capture_rate_raw()))
    print("CaptureRate: {}".format(cdsp.get_capture_rate()))
    cdsp.set_update_interval(500)
    print("UpdateInterval: {}".format(cdsp.get_update_interval()))
    print("RateAdjust: {}".format(cdsp.get_rate_adjust()))

