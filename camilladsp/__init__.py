"""
Python library for communicating with CamillaDSP.
"""

from camilladsp.camilladsp import CamillaClient
from camilladsp.datastructures import (
    ProcessingState,
    StopReason,
)
from camilladsp.exceptions import (
    CamillaError,
    InvalidRequestError,
    InvalidValueError,
    RateLimitExceededError,
    ShutdownInProgressError,
    ConfigReadError,
    ConfigValidationError,
    InvalidFaderError,
    UnknownError,
)

from camilladsp.versions import VERSION
