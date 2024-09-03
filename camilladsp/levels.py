"""
Python library for communicating with CamillaDSP.

This module contains commands for reading levels.
"""

from typing import Dict, List
import math

from .commandgroup import _CommandGroup


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

    def capture_rms(self) -> List[float]:
        """
        Get capture signal level rms in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetCaptureSignalRms")
        return sigrms

    def playback_rms(self) -> List[float]:
        """
        Get playback signal level rms in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetPlaybackSignalRms")
        return sigrms

    def capture_peak(self) -> List[float]:
        """
        Get capture signal level peak in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetCaptureSignalPeak")
        return sigpeak

    def playback_peak(self) -> List[float]:
        """
        Get playback signal level peak in dB for the last processed chunk.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetPlaybackSignalPeak")
        return sigpeak

    def playback_peak_since(self, interval: float) -> List[float]:
        """
        Get playback signal level peak in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigpeak = self.client.query("GetPlaybackSignalPeakSince", arg=float(interval))
        return sigpeak

    def playback_rms_since(self, interval: float) -> List[float]:
        """
        Get playback signal level rms in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigrms = self.client.query("GetPlaybackSignalRmsSince", arg=float(interval))
        return sigrms

    def capture_peak_since(self, interval: float) -> List[float]:
        """
        Get capture signal level peak in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigpeak = self.client.query("GetCaptureSignalPeakSince", arg=float(interval))
        return sigpeak

    def capture_rms_since(self, interval: float) -> List[float]:
        """
        Get capture signal level rms in dB for the last `interval` seconds.
        Full scale is 0 dB. Returns a list with one element per channel.

        Args:
            interval (float): Length of interval in seconds.
        """
        sigrms = self.client.query("GetCaptureSignalRmsSince", arg=float(interval))
        return sigrms

    def playback_peak_since_last(self) -> List[float]:
        """
        Get playback signal level peak in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetPlaybackSignalPeakSinceLast")
        return sigpeak

    def playback_rms_since_last(self) -> List[float]:
        """
        Get playback signal level rms in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetPlaybackSignalRmsSinceLast")
        return sigrms

    def capture_peak_since_last(self) -> List[float]:
        """
        Get capture signal level peak in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigpeak = self.client.query("GetCaptureSignalPeakSinceLast")
        return sigpeak

    def capture_rms_since_last(self) -> List[float]:
        """
        Get capture signal level rms in dB since the last read by the same client.
        Full scale is 0 dB. Returns a list with one element per channel.
        """
        sigrms = self.client.query("GetCaptureSignalRmsSinceLast")
        return sigrms

    def levels(self) -> Dict[str, List[float]]:
        """
        Get all signal levels in dB for the last processed chunk.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.
        """
        siglevels = self.client.query("GetSignalLevels")
        return siglevels

    def levels_since(self, interval: float) -> Dict[str, List[float]]:
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

    def levels_since_last(self) -> Dict[str, List[float]]:
        """
        Get all signal levels in dB since the last read by the same client.
        Full scale is 0 dB.
        The values are returned as a json object with keys
        `playback_peak`, `playback_rms`, `capture_peak` and `capture_rms`.
        Each dict item is a list with one element per channel.
        """
        siglevels = self.client.query("GetSignalLevelsSinceLast")
        return siglevels

    def peaks_since_start(self) -> Dict[str, List[float]]:
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
