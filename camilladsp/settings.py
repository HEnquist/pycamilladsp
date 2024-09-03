"""
Python library for communicating with CamillaDSP.

This module contains commands for various settings.
"""

from .commandgroup import _CommandGroup


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
