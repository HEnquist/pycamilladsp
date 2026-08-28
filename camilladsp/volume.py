"""
Python library for communicating with CamillaDSP.

This module contains commands for mute and volume control.
"""

from typing import Any, Dict, List, Optional

from .commandgroup import _CommandGroup
from .datastructures import Fader


class Volume(_CommandGroup):
    """
    Collection of methods for volume and mute control
    """

    default_min_vol = -150.0
    default_max_vol = 50.0

    def _limit_args(
        self, min_limit: Optional[float], max_limit: Optional[float]
    ) -> Dict[str, Any]:
        """
        Build the optional `min` and `max` arguments for the volume adjust commands.
        Both are sent if either one is given, since CamillaDSP defaults the
        omitted one to the full range.
        """
        if min_limit is None and max_limit is None:
            return {}
        maxlim = max_limit if max_limit is not None else self.default_max_vol
        minlim = min_limit if min_limit is not None else self.default_min_vol
        return {"min": float(minlim), "max": float(maxlim)}

    def all(self) -> List[Fader]:
        """
        Get volume and mute for all faders with a single call.

        Returns:
            List[Fader]: A list of one object per fader, each with `volume` and `mute` properties.
        """
        faders = self.client.query("GetFaders")
        return faders

    def main_volume(self) -> float:
        """
        Get current main volume setting in dB.
        Equivalent to calling `volume(0)`.

        Returns:
            float: Current volume setting.
        """
        vol = self.client.query("GetVolume")
        return float(vol)

    def set_main_volume(self, value: float):
        """
        Set main volume in dB.
        Equivalent to calling `set_volume(0)`.

        Args:
            value (float): New volume in dB.
        """
        self.client.query("SetVolume", value=float(value))

    def adjust_main_volume(
        self,
        value: float,
        min_limit: Optional[float] = None,
        max_limit: Optional[float] = None,
    ) -> float:
        """
        Adjust main volume in dB.
        Equivalent to calling `adjust_volume(0, ...)`.
        Positive values increase the volume, negative decrease.
        The resulting volume is limited to the range -150 to +50 dB.
        This default range can be reduced via the optional
        `min_limit` and/or `max_limit` arguments.

        Args:
            value (float): Volume adjustment in dB.
            min_limit (float): Lower volume limit to clamp volume at.
            max_limit (float): Upper volume limit to clamp volume at.

        Returns:
            float: New volume setting.
        """
        limits = self._limit_args(min_limit, max_limit)
        new_vol = self.client.query("AdjustVolume", value=float(value), **limits)
        return float(new_vol)

    def volume(self, fader: int) -> float:
        """
        Get current volume setting for the given fader in dB.

        Args:
            fader (int): Fader to read.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            float: Current volume setting.
        """
        _fader, vol = self.client.query("GetFaderVolume", fader=int(fader))
        return float(vol)

    def set_volume(self, fader: int, vol: float):
        """
        Set volume for the given fader in dB.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            vol (float): New volume setting.
        """
        self.client.query("SetFaderVolume", fader=int(fader), value=float(vol))

    def set_volume_external(self, fader: int, vol: float):
        """
        Special command for setting the volume when a "Loudness" filter
        is being combined with an external volume control (without a "Volume" filter).
        Set volume for the given fader in dB.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            vol (float): New volume setting.
        """
        self.client.query("SetFaderExternalVolume", fader=int(fader), value=float(vol))

    def adjust_volume(
        self,
        fader: int,
        value: float,
        min_limit: Optional[float] = None,
        max_limit: Optional[float] = None,
    ) -> float:
        """
        Adjust volume for the given fader in dB.
        Positive values increase the volume, negative decrease.
        The resulting volume is limited to the range -150 to +50 dB.
        This default range can be reduced via the optional
        `min_limit` and/or `max_limit` arguments.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            value (float): Volume adjustment in dB.
            min_limit (float): Lower volume limit to clamp volume at.
            max_limit (float): Upper volume limit to clamp volume at.


        Returns:
            float: New volume setting.
        """
        limits = self._limit_args(min_limit, max_limit)
        _fader, new_vol = self.client.query(
            "AdjustFaderVolume", fader=int(fader), value=float(value), **limits
        )
        return float(new_vol)

    def main_mute(self) -> bool:
        """
        Get current main mute setting.
        Equivalent to calling `mute(0)`.

        Returns:
            bool: True if muted, False otherwise.
        """
        mute = self.client.query("GetMute")
        return bool(mute)

    def set_main_mute(self, value: bool):
        """
        Set main mute, true or false.
        Equivalent to calling `set_mute(0)`.

        Args:
            value (bool): New mute setting.
        """
        self.client.query("SetMute", value=bool(value))

    def toggle_main_mute(self) -> bool:
        """
        Toggle main mute.
        Equivalent to calling `toggle_mute(0)`.

        Returns:
            bool: True if the new status is muted, False otherwise.
        """
        new_mute = self.client.query("ToggleMute")
        return bool(new_mute)

    def mute(self, fader: int) -> bool:
        """
        Get current mute setting for a fader.

        Args:
            fader (int): Fader to read.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            bool: True if muted, False otherwise.
        """
        _fader, mute = self.client.query("GetFaderMute", fader=int(fader))
        return bool(mute)

    def set_mute(self, fader: int, value: bool):
        """
        Set mute status for a fader, true or false.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.
            value (bool): New mute setting.
        """
        self.client.query("SetFaderMute", fader=int(fader), value=bool(value))

    def toggle_mute(self, fader: int) -> bool:
        """
        Toggle mute status for a fader.

        Args:
            fader (int): Fader to control.
                Selected using an integer, 0 for `Main` and 1 to 4 for `Aux1` to `Aux4`.

        Returns:
            bool: True if the new status is muted, False otherwise.
        """
        _fader, new_mute = self.client.query("ToggleFaderMute", fader=int(fader))
        return new_mute
