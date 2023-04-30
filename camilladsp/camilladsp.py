"""
Python library for communicating with CamillaDSP.
"""

from enum import Enum, auto
import json
import math
from typing import Optional
from threading import Lock
import yaml
from websocket import create_connection, WebSocket  # type: ignore

_VERSION = ("2", "0", "0")

_STANDARD_RATES = (
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
    705600,
    768000,
)


class ProcessingState(Enum):
    """
    An enum representing the different processing states of CamillaDSP.
    """

    RUNNING = auto()
    PAUSED = auto()
    INACTIVE = auto()
    STARTING = auto()
    STALLED = auto()


def _state_from_string(value: str) -> Optional[ProcessingState]:
    if value == "Running":
        return ProcessingState.RUNNING
    if value == "Paused":
        return ProcessingState.PAUSED
    if value == "Inactive":
        return ProcessingState.INACTIVE
    if value == "Starting":
        return ProcessingState.STARTING
    if value == "Stalled":
        return ProcessingState.STALLED
    return None


class StopReason(Enum):
    """
    An enum representing the possible reasons why CamillaDSP stopped processing.
    The StopReason enums carry additional data:
    - CAPTUREERROR and PLAYBACKERROR:
      Carries the error message as a string.
    - CAPTUREFORMATCHANGE and PLAYBACKFORMATCHANGE:
      Carries the estimated new sample rate as an integer.
      A value of 0 means the new rate is unknown.

    The additional data can be accessed by reading the `data` property:
    ```python
    reason = cdsp.get_stop_reason()
    if reason == StopReason.CAPTUREERROR:
        error_msg = reason.data
        print(f"Capture failed, error: {error_msg}")
    ```
    """

    NONE = auto()
    DONE = auto()
    CAPTUREERROR = auto()
    PLAYBACKERROR = auto()
    CAPTUREFORMATCHANGE = auto()
    PLAYBACKFORMATCHANGE = auto()

    def __new__(cls, value):
        obj = object.__new__(cls)
        obj._value_ = value
        obj._data = None
        return obj

    def set_data(self, value):
        """
        Set the custom data property of the enum.
        """
        self._data = value

    @property
    def data(self):
        """Getter for the data property"""
        return self._data


def _reason_from_reply(value):
    if isinstance(value, dict):
        reason, data = next(iter(value.items()))
    else:
        reason = value
        data = None

    if reason == "None":
        reasonenum = StopReason.NONE
    elif reason == "Done":
        reasonenum = StopReason.DONE
    elif reason == "CaptureError":
        reasonenum = StopReason.CAPTUREERROR
    elif reason == "PlaybackError":
        reasonenum = StopReason.PLAYBACKERROR
    elif reason == "CaptureFormatChange":
        reasonenum = StopReason.CAPTUREFORMATCHANGE
    elif reason == "PlaybackFormatChange":
        reasonenum = StopReason.PLAYBACKFORMATCHANGE
    else:
        raise ValueError(f"Invalid value for StopReason: {value}")
    reasonenum.set_data(data)
    return reasonenum


class CamillaError(ValueError):
    """
    A class representing errors returned by CamillaDSP.
    """


class CamillaConnection:
    """
    Class for communicating with CamillaDSP.
    """

    # pylint: disable=too-many-public-methods

    # ========================= Internal use =========================

    def __init__(self, host: str, port: int):
        """
        Connect to CamillaDSP on the specified host and port.
        """
        self._host = host
        self._port = int(port)
        self._ws: Optional[WebSocket] = None
        self._version: Optional[tuple[str, str, str]] = None
        self._lock = Lock()

    def _query(self, command: str, arg=None):
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
        self._version = (version[0], version[1], version[2])

    # ========================= Connection management =========================

    def connect(self):
        """
        Connect to the websocket of CamillaDSP.
        """
        try:
            with self._lock:
                self._ws = create_connection(f"ws://{self._host}:{self._port}")
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

    # ========================= General info =========================

    def get_version(self):
        """Read CamillaDSP version, returns a tuple of (major, minor, patch)."""
        return self._version

    def get_supported_device_types(self) -> tuple[list[str], list[str]]:
        """
        Read what device types the running CamillaDSP process supports.
        Returns a tuple with two lists of device types,
        the first for playback and the second for capture.

        Returns:
            tuple[list[str], list[str]]: A tuple containing two lists,
                with the supported capture and playback device types.
        """
        (playback, capture) = self._query("GetSupportedDeviceTypes")
        return (playback, capture)

    def get_library_version(self) -> tuple[str, str, str]:
        """Read pycamilladsp version, returns a tuple of (major, minor, patch)."""
        return _VERSION

    # ========================= CamillaDSP state =========================

    def get_state(self) -> Optional[ProcessingState]:
        """
        Get current processing state.

        Returns:
            ProcessingState | None: Current processing state.
        """
        state = self._query("GetState")
        return _state_from_string(state)

    def get_stop_reason(self) -> StopReason:
        """
        Get reason why processing stopped.

        Returns:
            StopReason: Stop reason enum variant.
        """
        reason = self._query("GetStopReason")
        return _reason_from_reply(reason)

    # ========================= Basic commands =========================

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

    # ========================= Status parameter update interval =========================

    def get_update_interval(self) -> int:
        """
        Get current update interval in ms.

        Returns:
            int: Current update interval.
        """
        interval = self._query("GetUpdateInterval")
        return int(interval)

    def set_update_interval(self, value: int):
        """
        Set current update interval in ms.

        Args:
            value (int): New update interval.
        """
        self._query("SetUpdateInterval", arg=value)

    # ========================= Getters for status parameters =========================

    def get_rate_adjust(self) -> float:
        """
        Get current value for rate adjust, 1.0 means 1:1 resampling.

        Returns:
            float: Rate adjust value.
        """
        adj = self._query("GetRateAdjust")
        return float(adj)

    def get_buffer_level(self) -> int:
        """
        Get current buffer level of the playback device.

        Returns:
            int: Buffer level in frames.
        """
        level = self._query("GetBufferLevel")
        return int(level)

    def get_clipped_samples(self) -> int:
        """
        Get number of clipped samples since the config was loaded.

        Returns:
            int: Number of clipped samples.
        """
        clipped = self._query("GetClippedSamples")
        return int(clipped)

    def get_processing_load(self) -> float:
        """
        Get processing load in percent.

        Returns:
            float: Current load.
        """
        load = self._query("GetProcessingLoad")
        return float(load)

    # ========================= Signal level monitoring =========================

    def get_signal_range(self) -> float:
        """
        Get signal range for the last processed chunk. Full scale is 2.0.
        """
        sigrange = self._query("GetSignalRange")
        return float(sigrange)

    def get_signal_range_decibel(self) -> float:
        """
        Get current signal range in dB for the last processed chunk.
        Full scale is 0 dB.
        """
        sigrange = self.get_signal_range()
        if sigrange > 0.0:
            range_decibel = 20.0 * math.log10(sigrange / 2.0)
        else:
            range_decibel = -1000
        return range_decibel

    def get_capture_signal_rms(self) -> list[float]:
        """
        Get capture signal level rms in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self._query("GetCaptureSignalRms")
        return sigrms

    def get_playback_signal_rms(self) -> list[float]:
        """
        Get playback signal level rms in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self._query("GetPlaybackSignalRms")
        return sigrms

    def get_capture_signal_peak(self) -> list[float]:
        """
        Get capture signal level peak in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self._query("GetCaptureSignalPeak")
        return sigpeak

    def get_playback_signal_peak(self) -> list[float]:
        """
        Get playback signal level peak in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self._query("GetPlaybackSignalPeak")
        return sigpeak

    def get_playback_signal_peak_since(self, interval: float) -> list[float]:
        """
        Get playback signal level peak in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigpeak = self._query("GetPlaybackSignalPeakSince", arg=float(interval))
        return sigpeak

    def get_playback_signal_rms_since(self, interval: float) -> list[float]:
        """
        Get playback signal level rms in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigrms = self._query("GetPlaybackSignalRmsSince", arg=float(interval))
        return sigrms

    def get_capture_signal_peak_since(self, interval: float) -> list[float]:
        """
        Get capture signal level peak in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigpeak = self._query("GetCaptureSignalPeakSince", arg=float(interval))
        return sigpeak

    def get_capture_signal_rms_since(self, interval: float) -> list[float]:
        """
        Get capture signal level rms in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigrms = self._query("GetCaptureSignalRmsSince", arg=float(interval))
        return sigrms

    def get_playback_signal_peak_since_last(self) -> list[float]:
        """
        Get playback signal level peak in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self._query("GetPlaybackSignalPeakSinceLast")
        return sigpeak

    def get_playback_signal_rms_since_last(self) -> list[float]:
        """
        Get playback signal level rms in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self._query("GetPlaybackSignalRmsSinceLast")
        return sigrms

    def get_capture_signal_peak_since_last(self) -> list[float]:
        """
        Get capture signal level peak in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self._query("GetCaptureSignalPeakSinceLast")
        return sigpeak

    def get_capture_signal_rms_since_last(self) -> list[float]:
        """
        Get capture signal level rms in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self._query("GetCaptureSignalRmsSinceLast")
        return sigrms

    def get_signal_levels(self) -> dict[str, list[float]]:
        """
        Get all signal levels in dB for the last processed chunk.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.
        """
        siglevels = self._query("GetSignalLevels")
        return siglevels

    def get_signal_levels_since(self, interval: float) -> dict[str, list[float]]:
        """
        Get all signal levels in dB for the last `interval` seconds.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        siglevels = self._query("GetSignalLevelsSince", arg=float(interval))
        return siglevels

    def get_signal_levels_since_last(self) -> dict[str, list[float]]:
        """
        Get all signal levels in dB since the last read by the same client.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.
        """
        siglevels = self._query("GetSignalLevelsSinceLast")
        return siglevels

    def get_signal_peaks_since_start(self) -> dict[str, list[float]]:
        """
        Get the playback and capture peak level since processing started.
        The values are returned as a json object with keys `playback` and `capture`.
        """
        peaks = self._query("GetSignalPeaksSinceStart")
        return peaks

    def reset_signal_peaks_since_start(self):
        """
        Reset the peak level values.
        """
        self._query("ResetSignalPeaksSinceStart")

    # ========================= Volume and mute control =========================

    def get_volume(self) -> float:
        """
        Get current main volume setting in dB.
        Equivalent to calling `get_fader_volume()` with `fader=0`.

        Returns:
            float: Current volume setting.
        """
        vol = self._query("GetVolume")
        return float(vol)

    def set_volume(self, value: float):
        """
        Set main volume in dB.
        Equivalent to calling `set_fader_volume()` with `fader=0`.

        Args:
            value (float): New volume in dB.
        """
        self._query("SetVolume", arg=float(value))

    def get_mute(self) -> bool:
        """
        Get current main mute setting.
        Equivalent to calling `get_fader_mute()` with `fader=0`.

        Returns:
            bool: True if muted, False otherwise.
        """
        mute = self._query("GetMute")
        return bool(mute)

    def set_mute(self, value: bool):
        """
        Set main mute, true or false.
        Equivalent to calling `set_fader_mute()` with `fader=0`.

        Args:
            value (bool): New mute setting.
        """
        self._query("SetMute", arg=bool(value))

    def get_fader_volume(self, fader: int) -> float:
        """
        Get current volume setting for the given fader in dB.

        Args:
            fader (int): Fader to read.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            float: Current volume setting.
        """
        _fader, vol = self._query("GetFaderVolume", arg=int(fader))
        return float(vol)

    def set_fader_volume(self, fader: int, vol: float):
        """
        Set volume for the given fader in dB.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            vol (float): New volume setting.
        """
        _fader = self._query("SetFaderVolume", arg=(int(fader), float(vol)))

    def set_fader_external_volume(self, fader: int, vol: float):
        """
        Special command for setting the volume when a Loudness filter
        is being combined with an external volume control (without a Volume filter).
        Set volume for the given fader in dB.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            vol (float): New volume setting.
        """
        _fader = self._query("SetFaderExternalVolume", arg=(int(fader), float(vol)))

    def adjust_fader_volume(self, fader: int, value: float) -> float:
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
        _fader, new_vol = self._query(
            "AdjustFaderVolume", arg=(int(fader), float(value))
        )
        return float(new_vol)

    def get_fader_mute(self, fader: int) -> bool:
        """
        Get current mute setting for a fader.

        Args:
            fader (int): Fader to read.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            bool: True if muted, False otherwise.
        """
        _fader, mute = self._query("GetFaderMute", arg=int(fader))
        return bool(mute)

    def set_fader_mute(self, fader: int, value: bool):
        """
        Set mute status for a fader, true or false.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            value (bool): New mute setting.
        """
        _fader = self._query("SetFaderMute", arg=(int(fader), bool(value)))

    def toggle_fader_mute(self, fader: int) -> bool:
        """
        Toggle mute status for a fader.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            bool: True if the new status is muted, False otherwise.
        """
        _fader, new_mute = self._query("SetFaderMute", arg=int(fader))
        return new_mute

    # ========================= Sample rate monitoring =========================

    def get_capture_rate_raw(self) -> int:
        """
        Get current capture rate, raw value.

        Returns:
            int: The current raw capture rate.
        """
        rate = self._query("GetCaptureRate")
        return int(rate)

    def get_capture_rate(self) -> Optional[int]:
        """
        Get current capture rate.
        Returns the nearest common rate, as long as it's within +-4% of the measured value.

        Returns:
            int: The current capture rate.
        """
        rate = self.get_capture_rate_raw()
        if 0.96 * _STANDARD_RATES[0] < rate < 1.04 * _STANDARD_RATES[-1]:
            nearest = min(_STANDARD_RATES, key=lambda val: abs(val - rate))
            if 0.96 < rate / nearest < 1.04:
                return nearest
        return None

    # ========================= Configuration management =========================

    def get_config_name(self) -> Optional[str]:
        """
        Get path to current config file.

        Returns:
            str | None: Path to config file, or None.
        """
        name = self._query("GetConfigName")
        return name

    def set_config_name(self, value: str):
        """
        Set path to config file.

        Args:
            value (str): Path to config file.
        """
        self._query("SetConfigName", arg=value)

    def get_config_raw(self) -> Optional[str]:
        """
        Get the active configuation in yaml format as a string.

        Returns:
            str | None: Current config as a raw yaml string, or None.
        """
        config_string = self._query("GetConfig")
        return config_string

    def set_config_raw(self, config_string: str):
        """
        Upload a new configuation in yaml format as a string.

        Args:
            config_string (str): Config as yaml string.
        """
        self._query("SetConfig", arg=config_string)

    def get_config(self) -> Optional[dict]:
        """
        Get the active configuation as a Python object.

        Returns:
            dict | None: Current config as a Python dict, or None.
        """
        config_string = self.get_config_raw()
        if config_string is None:
            return None
        config_object = yaml.safe_load(config_string)
        return config_object

    def get_previous_config(self) -> Optional[dict]:
        """
        Get the previously active configuation as a Python object.

        Returns:
            dict | None: Previous config as a Python dict, or None.
        """
        config_string = self._query("GetPreviousConfig")
        config_object = yaml.safe_load(config_string)
        return config_object

    def read_config(self, config_string: str) -> dict:
        """
        Read a config from yaml string and return the contents
        as a Python object, with defaults filled out with their default values.

        Args:
            config_string (str): A config as raw yaml string.

        Returns:
            dict | None: Parsed config as a Python dict.
        """
        config_raw = self._query("ReadConfig", arg=config_string)
        config_object = yaml.safe_load(config_raw)
        return config_object

    def read_config_file(self, filename: str) -> dict:
        """
        Read a config file from disk and return the contents as a Python object.

        Args:
            filename (str): Path to a config file.

        Returns:
            dict | None: Parsed config as a Python dict.
        """
        config_raw = self._query("ReadConfigFile", arg=filename)
        config = yaml.safe_load(config_raw)
        return config

    def set_config(self, config_object: dict):
        """
        Upload a new configuation from a Python object.

        Args:
            config_object (dict): A configuration as a Python dict.
        """
        config_raw = yaml.dump(config_object)
        self.set_config_raw(config_raw)

    def validate_config(self, config_object: dict) -> dict:
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
        validated_string = self._query("ValidateConfig", arg=config_string)
        validated_object = yaml.safe_load(validated_string)
        return validated_object

    def get_config_title(self) -> Optional[str]:
        """
        Get the title of the current configuration.

        Returns:
            str | None: Config title if defined, else None.
        """
        title = self._query("GetConfigTitle")
        return title

    def get_config_description(self) -> Optional[str]:
        """
        Get the title of the current configuration.

        Returns:
            str | None: Config description if defined, else None.
        """
        desc = self._query("GetConfigDescription")
        return desc
