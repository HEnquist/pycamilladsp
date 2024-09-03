"""
Python library for communicating with CamillaDSP.

This module contains commands for rate monitoring.
"""

from typing import Optional

from .commandgroup import _CommandGroup
from .datastructures import _STANDARD_RATES


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
