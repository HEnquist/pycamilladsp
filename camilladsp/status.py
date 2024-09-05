"""
Python library for communicating with CamillaDSP.

This module contains commands for reading status.
"""

from .commandgroup import _CommandGroup


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
