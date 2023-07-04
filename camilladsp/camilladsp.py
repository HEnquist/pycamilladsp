"""
Python library for communicating with CamillaDSP.

The main component is the `CamillaClient` class.
This class handles the communication over websocket with the CamillaDSP process.

The various commands are grouped on helper classes that are instantiated
by the CamillaClient class.
For example volume controls are handled by the `Volume` class.
These methods are accessible via the `volume` property of the CamillaClient.
Reading the main volume is then done by calling `my_client.volume.main()`.
"""


import json
import math
from typing import Optional
from threading import Lock
import yaml
from websocket import create_connection, WebSocket  # type: ignore

from .datastructures import (
    ProcessingState,
    StopReason,
    _STANDARD_RATES,
    _state_from_string,
    _reason_from_reply,
)

_VERSION = ("2", "0", "0")


class CamillaError(ValueError):
    """
    A class representing errors returned by CamillaDSP.
    """


class _CamillaWS:
    def __init__(self, host: str, port: int):
        """
        Create a new CamillaWS.

        Args:
            host (str): Hostname where CamillaDSP runs.
            port (int): Port number of the CamillaDSP websocket server.
        """
        self._host = host
        self._port = int(port)
        self._ws: Optional[WebSocket] = None
        self.cdsp_version: Optional[tuple[str, str, str]] = None
        self._lock = Lock()

    def query(self, command: str, arg=None):
        """
        Send a command and return the response.

        Args:
            command (str): The command to send.
            arg: Parameter to send with the command.

        Returns:
            Any | None: The return value for commands that return values, None for others.
        """
        if self._ws is None:
            raise IOError("Not connected to CamillaDSP")
        if arg is not None:
            query = json.dumps({command: arg})
        else:
            query = json.dumps(command)
        try:
            with self._lock:
                self._ws.send(query)
                rawrepl = self._ws.recv()
        except Exception as err:
            self._ws = None
            raise IOError("Lost connection to CamillaDSP") from err
        return self._handle_reply(command, rawrepl)

    def _handle_reply(self, command: str, rawreply: str):
        try:
            reply = json.loads(rawreply)
            value = None
            if command in reply:
                state = reply[command]["result"]
                if "value" in reply[command]:
                    value = reply[command]["value"]
                if state == "Error" and value is not None:
                    raise CamillaError(value)
                if state == "Error" and value is None:
                    raise CamillaError("Command returned an error")
                if state == "Ok" and value is not None:
                    return value
                return None
            raise IOError(f"Invalid response received: {rawreply}")
        except json.JSONDecodeError as err:
            raise IOError(f"Invalid response received: {rawreply}") from err

    def _update_version(self, resp: str):
        version = resp.split(".", 3)
        if len(version) < 3:
            version.extend([""] * (3 - len(version)))
        self.cdsp_version = (version[0], version[1], version[2])

    def connect(self):
        """
        Connect to the websocket of CamillaDSP.
        """
        try:
            with self._lock:
                self._ws = create_connection(f"ws://{self._host}:{self._port}")
            rawvers = self.query("GetVersion")
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
            except Exception as _e:  # pylint: disable=broad-exception-caught
                pass
            self._ws = None

    def is_connected(self):
        """
        Is websocket connected?

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._ws is not None


class _CommandGroup:
    """
    Collection of methods
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, client: _CamillaWS):
        self.client = client


class Status(_CommandGroup):
    """
    Collection of methods for reading status
    """

    def rate_adjust(self) -> float:
        """
        Get current value for rate adjust, 1.0 means 1:1 resampling.

        Returns:
            float: Rate adjust value.
        """
        adj = self.client.query("GetRateAdjust")
        return float(adj)

    def buffer_level(self) -> int:
        """
        Get current buffer level of the playback device.

        Returns:
            int: Buffer level in frames.
        """
        level = self.client.query("GetBufferLevel")
        return int(level)

    def clipped_samples(self) -> int:
        """
        Get number of clipped samples since the config was loaded.

        Returns:
            int: Number of clipped samples.
        """
        clipped = self.client.query("GetClippedSamples")
        return int(clipped)

    def processing_load(self) -> float:
        """
        Get processing load in percent.

        Returns:
            float: Current load.
        """
        load = self.client.query("GetProcessingLoad")
        return float(load)


class Levels(_CommandGroup):
    """
    Collection of methods for level monitoring
    """

    def range(self) -> float:
        """
        Get signal range for the last processed chunk. Full scale is 2.0.
        """
        sigrange = self.client.query("GetSignalRange")
        return float(sigrange)

    def range_decibel(self) -> float:
        """
        Get current signal range in dB for the last processed chunk.
        Full scale is 0 dB.
        """
        sigrange = self.range()
        if sigrange > 0.0:
            range_decibel = 20.0 * math.log10(sigrange / 2.0)
        else:
            range_decibel = -1000
        return range_decibel

    def capture_rms(self) -> list[float]:
        """
        Get capture signal level rms in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetCaptureSignalRms")
        return sigrms

    def playback_rms(self) -> list[float]:
        """
        Get playback signal level rms in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetPlaybackSignalRms")
        return sigrms

    def capture_peak(self) -> list[float]:
        """
        Get capture signal level peak in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetCaptureSignalPeak")
        return sigpeak

    def playback_peak(self) -> list[float]:
        """
        Get playback signal level peak in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetPlaybackSignalPeak")
        return sigpeak

    def playback_peak_since(self, interval: float) -> list[float]:
        """
        Get playback signal level peak in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigpeak = self.client.query("GetPlaybackSignalPeakSince", arg=float(interval))
        return sigpeak

    def playback_rms_since(self, interval: float) -> list[float]:
        """
        Get playback signal level rms in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigrms = self.client.query("GetPlaybackSignalRmsSince", arg=float(interval))
        return sigrms

    def capture_peak_since(self, interval: float) -> list[float]:
        """
        Get capture signal level peak in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigpeak = self.client.query("GetCaptureSignalPeakSince", arg=float(interval))
        return sigpeak

    def capture_rms_since(self, interval: float) -> list[float]:
        """
        Get capture signal level rms in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigrms = self.client.query("GetCaptureSignalRmsSince", arg=float(interval))
        return sigrms

    def playback_peak_since_last(self) -> list[float]:
        """
        Get playback signal level peak in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetPlaybackSignalPeakSinceLast")
        return sigpeak

    def playback_rms_since_last(self) -> list[float]:
        """
        Get playback signal level rms in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetPlaybackSignalRmsSinceLast")
        return sigrms

    def capture_peak_since_last(self) -> list[float]:
        """
        Get capture signal level peak in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetCaptureSignalPeakSinceLast")
        return sigpeak

    def capture_rms_since_last(self) -> list[float]:
        """
        Get capture signal level rms in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetCaptureSignalRmsSinceLast")
        return sigrms

    def levels(self) -> dict[str, list[float]]:
        """
        Get all signal levels in dB for the last processed chunk.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.
        """
        siglevels = self.client.query("GetSignalLevels")
        return siglevels

    def levels_since(self, interval: float) -> dict[str, list[float]]:
        """
        Get all signal levels in dB for the last `interval` seconds.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        siglevels = self.client.query("GetSignalLevelsSince", arg=float(interval))
        return siglevels

    def levels_since_last(self) -> dict[str, list[float]]:
        """
        Get all signal levels in dB since the last read by the same client.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.
        """
        siglevels = self.client.query("GetSignalLevelsSinceLast")
        return siglevels

    def peaks_since_start(self) -> dict[str, list[float]]:
        """
        Get the playback and capture peak level since processing started.
        The values are returned as a json object with keys `playback` and `capture`.
        """
        peaks = self.client.query("GetSignalPeaksSinceStart")
        return peaks

    def reset_peaks_since_start(self):
        """
        Reset the peak level values.
        """
        self.client.query("ResetSignalPeaksSinceStart")


class Config(_CommandGroup):
    """
    Collection of methods for configuration management
    """

    def file_path(self) -> Optional[str]:
        """
        Get path to current config file.

        Returns:
            str | None: Path to config file, or None.
        """
        name = self.client.query("GetConfigFilePath")
        return name

    def set_file_path(self, value: str):
        """
        Set path to config file, without loading it.
        Call `reload()` to apply the new config file.

        Args:
            value (str): Path to config file.
        """
        self.client.query("SetConfigFilePath", arg=value)

    def active_raw(self) -> Optional[str]:
        """
        Get the active configuration in raw yaml format (as a string).

        Returns:
            str | None: Current config as a raw yaml string, or None.
        """
        config_string = self.client.query("GetConfig")
        return config_string

    def set_active_raw(self, config_string: str):
        """
        Upload and apply a new configuration in raw yaml format (as a string).

        Args:
            config_string (str): Config as yaml string.
        """
        self.client.query("SetConfig", arg=config_string)

    def active(self) -> Optional[dict]:
        """
        Get the active configuration as a Python object.

        Returns:
            dict | None: Current config as a Python dict, or None.
        """
        config_string = self.active_raw()
        if config_string is None:
            return None
        config_object = yaml.safe_load(config_string)
        return config_object

    def previous(self) -> Optional[dict]:
        """
        Get the previously active configuration as a Python object.

        Returns:
            dict | None: Previous config as a Python dict, or None.
        """
        config_string = self.client.query("GetPreviousConfig")
        config_object = yaml.safe_load(config_string)
        return config_object

    def parse_yaml(self, config_string: str) -> dict:
        """
        Parse a config from yaml string and return the contents
        as a Python object, with defaults filled out with their default values.

        Args:
            config_string (str): A config as raw yaml string.

        Returns:
            dict | None: Parsed config as a Python dict.
        """
        config_raw = self.client.query("ReadConfig", arg=config_string)
        config_object = yaml.safe_load(config_raw)
        return config_object

    def read_and_parse_file(self, filename: str) -> dict:
        """
        Read and parse a config file from disk and return the contents as a Python object.

        Args:
            filename (str): Path to a config file.

        Returns:
            dict | None: Parsed config as a Python dict.
        """
        config_raw = self.client.query("ReadConfigFile", arg=filename)
        config = yaml.safe_load(config_raw)
        return config

    def set_active(self, config_object: dict):
        """
        Upload and apply a new configuration from a Python object.

        Args:
            config_object (dict): A configuration as a Python dict.
        """
        config_raw = yaml.dump(config_object)
        self.set_active_raw(config_raw)

    def validate(self, config_object: dict) -> dict:
        """
        Validate a configuration object.
        Returns the validated config with all optional fields filled with defaults.
        Raises a CamillaError on errors.

        Args:
            config_object (dict): A configuration as a Python dict.

        Returns:
            dict | None: Validated config as a Python dict.
        """
        config_string = yaml.dump(config_object)
        validated_string = self.client.query("ValidateConfig", arg=config_string)
        validated_object = yaml.safe_load(validated_string)
        return validated_object

    def title(self) -> Optional[str]:
        """
        Get the title of the active configuration.

        Returns:
            str | None: Config title if defined, else None.
        """
        title = self.client.query("GetConfigTitle")
        return title

    def description(self) -> Optional[str]:
        """
        Get the title of the active configuration.

        Returns:
            str | None: Config description if defined, else None.
        """
        desc = self.client.query("GetConfigDescription")
        return desc


class Volume(_CommandGroup):
    """
    Collection of methods for volume and mute control
    """

    def main(self) -> float:
        """
        Get current main volume setting in dB.
        Equivalent to calling `get_fader_volume()` with `fader=0`.

        Returns:
            float: Current volume setting.
        """
        vol = self.client.query("GetVolume")
        return float(vol)

    def set_main(self, value: float):
        """
        Set main volume in dB.
        Equivalent to calling `set_fader()` with `fader=0`.

        Args:
            value (float): New volume in dB.
        """
        self.client.query("SetVolume", arg=float(value))

    def fader(self, fader: int) -> float:
        """
        Get current volume setting for the given fader in dB.

        Args:
            fader (int): Fader to read.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            float: Current volume setting.
        """
        _fader, vol = self.client.query("GetFaderVolume", arg=int(fader))
        return float(vol)

    def set_fader(self, fader: int, vol: float):
        """
        Set volume for the given fader in dB.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            vol (float): New volume setting.
        """
        self.client.query("SetFaderVolume", arg=(int(fader), float(vol)))

    def set_fader_external(self, fader: int, vol: float):
        """
        Special command for setting the volume when a "Loudness" filter
        is being combined with an external volume control (without a "Volume" filter).
        Set volume for the given fader in dB.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            vol (float): New volume setting.
        """
        self.client.query("SetFaderExternalVolume", arg=(int(fader), float(vol)))

    def adjust_fader(self, fader: int, value: float) -> float:
        """
        Adjust volume for the given fader in dB.
        Positive values increase the volume, negative decrease.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            value (float): Volume adjustment in dB.

        Returns:
            float: New volume setting.
        """
        _fader, new_vol = self.client.query(
            "AdjustFaderVolume", arg=(int(fader), float(value))
        )
        return float(new_vol)


class Mute(_CommandGroup):
    """
    Collection of methods for mute control
    """

    def main(self) -> bool:
        """
        Get current main mute setting.
        Equivalent to calling `get_fader()` with `fader=0`.

        Returns:
            bool: True if muted, False otherwise.
        """
        mute = self.client.query("GetMute")
        return bool(mute)

    def set_main(self, value: bool):
        """
        Set main mute, true or false.
        Equivalent to calling `set_fader()` with `fader=0`.

        Args:
            value (bool): New mute setting.
        """
        self.client.query("SetMute", arg=bool(value))

    def fader(self, fader: int) -> bool:
        """
        Get current mute setting for a fader.

        Args:
            fader (int): Fader to read.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            bool: True if muted, False otherwise.
        """
        _fader, mute = self.client.query("GetFaderMute", arg=int(fader))
        return bool(mute)

    def set_fader(self, fader: int, value: bool):
        """
        Set mute status for a fader, true or false.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            value (bool): New mute setting.
        """
        self.client.query("SetFaderMute", arg=(int(fader), bool(value)))

    def toggle_fader(self, fader: int) -> bool:
        """
        Toggle mute status for a fader.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            bool: True if the new status is muted, False otherwise.
        """
        _fader, new_mute = self.client.query("SetFaderMute", arg=int(fader))
        return new_mute


class RateMonitor(_CommandGroup):
    """
    Methods for rate monitoring
    """

    def capture_raw(self) -> int:
        """
        Get current capture rate, raw value.

        Returns:
            int: The current raw capture rate.
        """
        rate = self.client.query("GetCaptureRate")
        return int(rate)

    def capture(self) -> Optional[int]:
        """
        Get current capture rate.
        Returns the nearest common rate, as long as it's within +-4% of the measured value.

        Returns:
            int: The current capture rate.
        """
        rate = self.capture_raw()
        if 0.96 * _STANDARD_RATES[0] < rate < 1.04 * _STANDARD_RATES[-1]:
            nearest = min(_STANDARD_RATES, key=lambda val: abs(val - rate))
            if 0.96 < rate / nearest < 1.04:
                return nearest
        return None


class Settings(_CommandGroup):
    """
    Methods for various settings
    """

    def update_interval(self) -> int:
        """
        Get current update interval in ms.

        Returns:
            int: Current update interval.
        """
        interval = self.client.query("GetUpdateInterval")
        return int(interval)

    def set_update_interval(self, value: int):
        """
        Set current update interval in ms.

        Args:
            value (int): New update interval.
        """
        self.client.query("SetUpdateInterval", arg=value)


class General(_CommandGroup):
    """
    Basic commands
    """

    # ========================= CamillaDSP state =========================

    def state(self) -> Optional[ProcessingState]:
        """
        Get current processing state.

        Returns:
            ProcessingState | None: Current processing state.
        """
        state = self.client.query("GetState")
        return _state_from_string(state)

    def stop_reason(self) -> StopReason:
        """
        Get reason why processing stopped.

        Returns:
            StopReason: Stop reason enum variant.
        """
        reason = self.client.query("GetStopReason")
        return _reason_from_reply(reason)

    # ========================= Basic commands =========================

    def stop(self):
        """
        Stop processing and wait for new config if wait mode is active, else exit.
        """
        self.client.query("Stop")

    def exit(self):
        """
        Stop processing and exit.
        """
        self.client.query("Exit")

    def reload(self):
        """
        Reload config from disk.
        """
        self.client.query("Reload")

    def supported_device_types(self) -> tuple[list[str], list[str]]:
        """
        Read what device types the running CamillaDSP process supports.
        Returns a tuple with two lists of device types,
        the first for playback and the second for capture.

        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists,
                with the supported capture and playback device types.
        """
        (playback, capture) = self.client.query("GetSupportedDeviceTypes")
        return (playback, capture)

    def state_file_path(self) -> Optional[str]:
        """
        Get path to current state file.

        Returns:
            str | None: Path to state file, or None.
        """
        path = self.client.query("GetStateFilePath")
        return path

    def state_file_updated(self) -> bool:
        """
        Check if all changes have been saved to the state file.

        Returns:
            bool: True if all changes are saved.
        """
        updated = self.client.query("GetStateFileUpdated")
        return updated

    def list_playback_devices(self, value: str) -> list[tuple[str, str]]:
        """
        List the available playback devices for a given backend.
        Returns a list of tuples. Returns the system name and
        a descriptive name for each device.
        For some backends, those two names are identical.

        Returns:
            list[tuple[str, str]: A list containing tuples of two strings,
                with system device name and a descriptive name.
        """
        devs = self.client.query("GetAvailablePlaybackDevices", arg=value)
        return devs

    def list_capture_devices(self, value: str) -> list[tuple[str, str]]:
        """
        List the available capture devices for a given backend.
        Returns a list of tuples. Returns the system name and
        a descriptive name for each device.
        For some backends, those two names are identical.

        Returns:
            list[tuple[str, str]: A list containing tuples of two strings,
                with system device name and a descriptive name.
        """
        devs = self.client.query("GetAvailableCaptureDevices", arg=value)
        return devs


class Versions(_CommandGroup):
    """
    Version info
    """

    def camilladsp(self) -> Optional[tuple[str, str, str]]:
        """
        Read CamillaDSP version.

        Returns:
            tuple[list[str], list[str]] | None: A tuple containing the CamillaDSP version,
                as (major, minor, patch).
        """
        return self.client.cdsp_version

    def library(self) -> tuple[str, str, str]:
        """
        Read pyCamillaDSP library version.

        Returns:
            tuple[list[str], list[str]] | None: A tuple containing the pyCamillaDSP version,
                as (major, minor, patch).
        """
        return _VERSION


class CamillaClient(_CamillaWS):
    """
    Class for communicating with CamillaDSP.

    Args:
        host (str): Hostname where CamillaDSP runs.
        port (int): Port number of the CamillaDSP websocket server.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, host: str, port: int):
        """
        Create a new CamillaClient.

        Args:
            host (str): Hostname where CamillaDSP runs.
            port (int): Port number of the CamillaDSP websocket server.
        """
        super().__init__(host, port)

        self._volume = Volume(self)
        self._mute = Mute(self)
        self._rate = RateMonitor(self)
        self._levels = Levels(self)
        self._config = Config(self)
        self._status = Status(self)
        self._settings = Settings(self)
        self._general = General(self)
        self._versions = Versions(self)

    @property
    def volume(self) -> Volume:
        """
        A `Volume` instance for volume controls.
        """
        return self._volume

    @property
    def mute(self) -> Mute:
        """
        A `Mute` instance for mute controls.
        """
        return self._mute

    @property
    def rate(self) -> RateMonitor:
        """
        A `RateMonitor` instance for rate monitoring commands.
        """
        return self._rate

    @property
    def levels(self) -> Levels:
        """
        A `Levels` instance for signal level monitoring.
        """
        return self._levels

    @property
    def config(self) -> Config:
        """
        A `Config` instance for config management commands.
        """
        return self._config

    @property
    def status(self) -> Status:
        """
        A `Status` instance for status commands.
        """
        return self._status

    @property
    def settings(self) -> Settings:
        """
        A `Settings` instance for reading and writing settings.
        """
        return self._settings

    @property
    def general(self) -> General:
        """
        A `General` instance for basic commands.
        """
        return self._general

    @property
    def versions(self) -> Versions:
        """
        A `Versions` instance for version info.
        """
        return self._versions
