"""
Python library for communicating with CamillaDSP.

This module contains commands for reading version information.
"""

from typing import Tuple, Optional


from .commandgroup import _CommandGroup

VERSION = "3.0.0"


class Versions(_CommandGroup):
    """
    Version info
    """

    def camilladsp(self) -> Optional[Tuple[str, str, str]]:
        """
        Read CamillaDSP version.

        Returns:
            Tuple[List[str], List[str]] | None: A tuple containing the CamillaDSP version,
                as (major, minor, patch).
        """
        return self.client.cdsp_version

    def library(self) -> Tuple[str, str, str]:
        """
        Read pyCamillaDSP library version.

        Returns:
            Tuple[List[str], List[str]] | None: A tuple containing the pyCamillaDSP version,
                as (major, minor, patch).
        """
        ver = VERSION.split(".", 2)
        return (ver[0], ver[1], ver[2])
