"""
Python library for communicating with CamillaDSP.

This module contains commands for reading version information.
"""

from typing import Tuple, Optional


from .commandgroup import _CommandGroup

VERSION = "5.0.0"


class Versions(_CommandGroup):
    """
    Version info
    """

    def camilladsp(self) -> Optional[Tuple[str, str, str]]:
        """
        Read CamillaDSP version.

        Returns:
            Tuple[str, str, str] | None: A tuple containing the CamillaDSP version,
                as (major, minor, patch), or None if not connected.
        """
        return self.client.cdsp_version

    def library(self) -> Tuple[str, str, str]:
        """
        Read pyCamillaDSP library version.

        Returns:
            Tuple[str, str, str]: A tuple containing the pyCamillaDSP version,
                as (major, minor, patch).
        """
        ver = VERSION.split(".", 2)
        return (ver[0], ver[1], ver[2])
