"""
Python library for communicating with CamillaDSP.
"""

from camilladsp.camilladsp import CamillaClient, CamillaError
from camilladsp.datastructures import (
    ProcessingState,
    StopReason,
)

VERSION = "2.0.0-alpha2"
