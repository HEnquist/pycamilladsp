"""
Python library for communicating with CamillaDSP.
"""

from camilladsp.camilladsp import CamillaClient
from camilladsp.datastructures import (
    ProcessingState,
    StopReason,
    CamillaError,
)

from camilladsp.versions import VERSION
