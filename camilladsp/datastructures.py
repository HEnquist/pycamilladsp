"""
Various data structures used for communicating with CamillaDSP.
"""

from enum import Enum, auto
from typing import Optional

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

    The additional data can be accessed by reading the `data` property.
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
