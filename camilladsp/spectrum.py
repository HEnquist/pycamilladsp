"""
Python library for communicating with CamillaDSP.

This module contains commands for spectrum analysis.
"""

from typing import Any, Callable, Dict, List, Optional

from .commandgroup import _CommandGroup


class Spectrum(_CommandGroup):
    """
    Collection of methods for spectrum analysis.
    """

    def get_spectrum(
        self,
        side: str,
        min_freq: float,
        max_freq: float,
        n_bins: int,
        channel: Optional[int] = None,
    ) -> Dict[str, List[float]]:
        """
        Get a single frequency spectrum snapshot.

        Args:
            side (str): Which side to analyze, either ``"capture"`` or ``"playback"``.
            min_freq (float): Lower edge of the frequency range in Hz (must be > 0).
            max_freq (float): Upper edge of the frequency range in Hz (must be > ``min_freq``).
            n_bins (int): Number of output bins (must be >= 2).
            channel (int or None): Channel to analyze.
                ``None`` averages all channels; an integer selects a single channel (zero-based).

        Returns:
            dict: A dict with keys ``frequencies`` and ``magnitudes``,
            each a list of floats of length ``n_bins``.
        """
        if side not in ("capture", "playback"):
            raise ValueError("side must be one of: capture, playback")
        request = {
            "side": side,
            "channel": channel,
            "min_freq": float(min_freq),
            "max_freq": float(max_freq),
            "n_bins": int(n_bins),
        }
        return self.client.query("GetSpectrum", value=request)

    def subscribe_spectrum(
        self,
        callback: Callable[[Dict[str, Any]], Optional[bool]],
        side: str,
        min_freq: float,
        max_freq: float,
        n_bins: int,
        channel: Optional[int] = None,
        max_rate: Optional[float] = None,
    ):
        """
        Subscribe to spectrum events and call ``callback`` for each event.

        This method blocks until ``callback`` returns ``False``.

        Args:
            callback: Function that receives event payloads.
                Payload keys are ``frequencies`` and ``magnitudes``.
            side (str): Which side to analyze, either ``"capture"`` or ``"playback"``.
            min_freq (float): Lower edge of the frequency range in Hz (must be > 0).
            max_freq (float): Upper edge of the frequency range in Hz (must be > ``min_freq``).
            n_bins (int): Number of output bins (must be >= 2).
            channel (int or None): Channel to analyze.
                ``None`` averages all channels; an integer selects a single channel (zero-based).
            max_rate (float or None): Maximum push rate in Hz.
                When ``None``, CamillaDSP pushes at the natural hop rate.
        """
        if side not in ("capture", "playback"):
            raise ValueError("side must be one of: capture, playback")
        request: Dict[str, Any] = {
            "side": side,
            "channel": channel,
            "min_freq": float(min_freq),
            "max_freq": float(max_freq),
            "n_bins": int(n_bins),
        }
        if max_rate is not None:
            request["max_rate"] = float(max_rate)
        self.client.subscribe_events(
            command="SubscribeSpectrum",
            event_name="SpectrumEvent",
            callback=callback,
            value=request,
        )
