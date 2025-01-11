"""
Python library for communicating with CamillaDSP.

This module contains the base class for command groups.
"""

from .camillaws import _CamillaWS


class _CommandGroup:
    """
    Collection of methods
    """

    # pylint: disable=too-few-public-methods

    def __init__(self, client: _CamillaWS):
        self.client = client
