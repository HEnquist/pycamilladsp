"""
Python library for communicating with CamillaDSP.
"""

from camilladsp.camilladsp import CamillaClient, CamillaError
from camilladsp.datastructures import (
    ProcessingState,
    StopReason,
)
