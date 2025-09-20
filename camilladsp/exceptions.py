"""
Exceptions that may be raised by this library.
"""

from typing import Any, Optional


class CamillaError(Exception):
    """
    Base class for errors returned by CamillaDSP.
    The 'message' attribute holds an optional message as a string,
    while the 'value' attribute holds an optional value.
    """

    def __init__(self, message: Optional[str] = None, value: Any = None):
        self.message = message
        self.value = value
        super().__init__(self.message)


class ShutdownInProgressError(CamillaError):
    """
    CamillaDSP is shutting down and unable to handle any more commands.
    """


class RateLimitExceededError(CamillaError):
    """
    Too many requests were sent.
    """


class InvalidValueError(CamillaError):
    """
    An invalid value was supplied with a command.
    """


class InvalidRequestError(CamillaError):
    """
    An invalid command was sent.
    """


class InvalidFaderError(CamillaError):
    """
    An invalid fader index was supplied with a command.
    """


class ConfigValidationError(CamillaError):
    """
    The supplied config is invalid.
    """


class ConfigReadError(CamillaError):
    """
    An error occurred while reading the config file.
    """


class UnknownError(CamillaError):
    """
    An unknown error occurred.
    This should only happen if this library is used
    with a different version of CamillaDSP than it was intended for.
    """


def _raise_error(state: str, message: Optional[str], value: Any):
    """
    Raise the appropriate exception for the given error state.
    """
    if state == "RateLimitExceededError":
        raise RateLimitExceededError()
    if state == "ShutdownInProgressError":
        raise ShutdownInProgressError()
    if state == "InvalidValueError":
        raise InvalidValueError(message=message, value=value)
    if state == "InvalidRequestError":
        raise InvalidRequestError(message=message, value=value)
    if state == "InvalidFaderError":
        raise InvalidFaderError(value=value)
    if state == "ConfigValidationError":
        raise ConfigValidationError(message=message, value=value)
    if state == "ConfigReadError":
        raise ConfigReadError(message=message, value=value)
    raise UnknownError(message=message, value=value)
