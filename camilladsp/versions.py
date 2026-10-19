"""
Python library for communicating with CamillaDSP.

This module contains commands for reading version information.
"""

from typing import Optional


from .commandgroup import _CommandGroup

VERSION = "5.0.0-beta.1"


class Versions(_CommandGroup):
    """
    Version info
    """

    def camilladsp(self) -> Optional[str]:
        """
        Read CamillaDSP version.

        Returns:
            str | None: The CamillaDSP version as reported by CamillaDSP,
                for example "5.0.0", or None if not connected.
        """
        return self.client.cdsp_version

    def library(self) -> str:
        """
        Read pyCamillaDSP library version.

        Returns:
            str: The pyCamillaDSP version, for example "5.0.0".
        """
        return VERSION
