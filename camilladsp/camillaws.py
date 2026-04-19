"""
Python library for communicating with CamillaDSP.

This module contains the websocket connection class.
"""

from typing import Any, Callable, Dict, Tuple, Optional, Union
from threading import Lock
import json
from websocket import create_connection, WebSocket  # type: ignore

from .exceptions import (
    CamillaError,
    _raise_error,
)


class _CamillaWS:
    def __init__(self, host: str, port: int):
        """
        Create a new CamillaWS.

        Args:
            host (str): Hostname where CamillaDSP runs.
            port (int): Port number of the CamillaDSP websocket server.
        """
        self._host = host
        self._port = int(port)
        self._ws: Optional[WebSocket] = None
        self.cdsp_version: Optional[Tuple[str, str, str]] = None
        self._lock = Lock()

    def __del__(self):
        # Close the connection nicely instead of just dropping it,
        # which causes CamillaDSP to warn about a missing closing handshake.
        self.disconnect()

    def query(self, command: str, arg=None):
        """
        Send a command and return the response.

        Args:
            command (str): The command to send.
            arg: Parameter to send with the command.

        Returns:
            Any | None: The return value for commands that return values, None for others.
        """
        if self._ws is None:
            raise IOError("Not connected to CamillaDSP")
        rawrepl = self._send_and_receive(self._make_query(command, arg))
        return self._handle_reply(command, rawrepl)

    @staticmethod
    def _make_query(command: str, arg=None) -> str:
        if arg is not None:
            return json.dumps({command: arg})
        return json.dumps(command)

    def _send_and_receive(self, query: str) -> Union[str, bytes]:
        if self._ws is None:
            raise IOError("Not connected to CamillaDSP")
        try:
            with self._lock:
                self._ws.send(query)
                return self._ws.recv()
        except Exception as err:
            self._ws = None
            raise IOError("Lost connection to CamillaDSP") from err

    def _receive_message(self) -> Union[str, bytes]:
        if self._ws is None:
            raise IOError("Not connected to CamillaDSP")
        try:
            with self._lock:
                return self._ws.recv()
        except Exception as err:
            self._ws = None
            raise IOError("Lost connection to CamillaDSP") from err

    def _handle_reply(self, command: str, rawreply: Union[str, bytes]):
        try:
            reply = json.loads(rawreply)
            if command in reply:
                response_data = reply[command]
                if "error" in response_data:
                    # generic error, the command was not recognized
                    raise CamillaError(message=response_data["error"])
                result = response_data["result"]
                state, message = self._handle_result(result)
                value = response_data.get("value")
                if state == "Ok":
                    return value
                _raise_error(state, message, value)
            raise IOError(f"Invalid response received: {rawreply!r}")
        except json.JSONDecodeError as err:
            raise IOError(f"Invalid response received: {rawreply!r}") from err

    def _handle_event_reply(self, event_name: str, rawreply: Union[str, bytes]):
        try:
            reply = json.loads(rawreply)
            if event_name not in reply:
                return None
            response_data = reply[event_name]
            result = response_data["result"]
            state, message = self._handle_result(result)
            value = response_data.get("value")
            if state == "Ok":
                return value
            _raise_error(state, message, value)
        except json.JSONDecodeError as err:
            raise IOError(f"Invalid response received: {rawreply!r}") from err

    def _handle_result(
        self, result: Union[str, Dict[str, str]]
    ) -> Tuple[str, Optional[str]]:
        if isinstance(result, str):
            return result, None
        return next(iter(result.items()))

    def _update_version(self, resp: str):
        version = resp.split(".", 3)
        if len(version) < 3:
            version.extend([""] * (3 - len(version)))
        self.cdsp_version = (version[0], version[1], version[2])

    def connect(self):
        """
        Connect to the websocket of CamillaDSP.
        """
        try:
            with self._lock:
                self._ws = create_connection(f"ws://{self._host}:{self._port}")
            rawvers = self.query("GetVersion")
            self._update_version(rawvers)
        except Exception as _e:
            self._ws = None
            raise

    def _receive_subscription_event(self, event_name: str):
        return self._handle_event_reply(event_name, self._receive_message())

    def _stop_subscription(self):
        if self._ws is None:
            return
        try:
            rawrepl = self._send_and_receive(self._make_query("StopSubscription"))
            self._handle_reply("StopSubscription", rawrepl)
        except (CamillaError, IOError):
            self._ws = None

    def subscribe_events(
        self,
        command: str,
        event_name: str,
        callback: Callable[[Any], Optional[bool]],
        arg=None,
    ):
        """
        Start a subscription and call `callback` for each incoming event value.

        This method blocks until the callback returns `False`, or an exception
        is raised. A `StopSubscription` command is sent before returning.

        Args:
            command (str): Subscription command to send.
            event_name (str): Name of event messages to listen for.
            callback: Function called with each event payload.
            arg: Optional parameter to send with the subscription command.
        """
        if not callable(callback):
            raise TypeError("callback must be callable")
        if self._ws is None:
            raise IOError("Not connected to CamillaDSP")

        self._handle_reply(command, self._send_and_receive(self._make_query(command, arg)))

        subscribed = True

        try:
            while True:
                event_data = self._receive_subscription_event(event_name)
                if event_data is None:
                    continue
                should_continue = callback(event_data)
                if should_continue is False:
                    break
        finally:
            if subscribed and self._ws is not None:
                self._stop_subscription()

    def disconnect(self):
        """
        Close the connection to the websocket.
        """
        if self._ws is not None:
            try:
                with self._lock:
                    self._ws.close()
            except Exception as _e:  # pylint: disable=broad-exception-caught
                pass
            self._ws = None

    def is_connected(self):
        """
        Is websocket connected?

        Returns:
            bool: True if connected, False otherwise.
        """
        return self._ws is not None
