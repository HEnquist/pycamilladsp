"""
Python library for communicating with CamillaDSP.

This module contains the websocket connection class.
"""

from typing import Any, Callable, Tuple, Optional, Union
from threading import Lock
import json
from websocket import create_connection, WebSocket  # type: ignore

from .exceptions import (
    CamillaError,
    ProcessingStoppedError,
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

    def query(self, command: str, **args):
        """
        Send a command and return the response.

        Args:
            command (str): The command to send.
            **args: Named arguments to send with the command.

        Returns:
            Any | None: The return value for commands that return values, None for others.
        """
        if self._ws is None:
            raise IOError("Not connected to CamillaDSP")
        rawrepl = self._send_and_receive(self._make_query(command, **args))
        return self._handle_reply(command, rawrepl)

    @staticmethod
    def _make_query(command: str, **args) -> str:
        return json.dumps({"command": command, **args})

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

    @staticmethod
    def _parse_reply(rawreply: Union[str, bytes]) -> dict:
        """
        Decode a reply and check that it has the expected shape.
        Raises a `CamillaError` if CamillaDSP did not recognize the command.
        """
        try:
            reply = json.loads(rawreply)
        except json.JSONDecodeError as err:
            raise IOError(f"Invalid response received: {rawreply!r}") from err
        if not isinstance(reply, dict) or "reply" not in reply:
            raise IOError(f"Invalid response received: {rawreply!r}")
        if reply["reply"] == "Invalid":
            # The command was not recognized, or is not valid in the current state.
            raise CamillaError(message=reply.get("error"))
        return reply

    def _handle_reply(self, command: str, rawreply: Union[str, bytes]):
        reply = self._parse_reply(rawreply)
        if reply["reply"] != command:
            raise IOError(f"Invalid response received: {rawreply!r}")
        return self._handle_result(reply, rawreply)

    def _handle_event_reply(self, event_name: str, rawreply: Union[str, bytes]):
        reply = self._parse_reply(rawreply)
        if reply["reply"] != event_name:
            return None
        return self._handle_result(reply, rawreply)

    def _handle_result(self, reply: dict, rawreply: Union[str, bytes]):
        """
        Return the value of a successful reply, or raise the matching exception.
        """
        result = reply.get("result")
        if not isinstance(result, str):
            raise IOError(f"Invalid response received: {rawreply!r}")
        value = reply.get("value")
        if result == "Ok":
            return value
        _raise_error(result, reply.get("message"), value)

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
        **args,
    ):
        """
        Start a subscription and call `callback` for each incoming event value.

        This method blocks until the callback returns `False`, or an exception
        is raised. A `StopSubscription` command is sent before returning.

        Args:
            command (str): Subscription command to send.
            event_name (str): Name of event messages to listen for.
            callback: Function called with each event payload.
            **args: Named arguments to send with the subscription command.
        """
        if not callable(callback):
            raise TypeError("callback must be callable")
        if self._ws is None:
            raise IOError("Not connected to CamillaDSP")

        self._handle_reply(
            command, self._send_and_receive(self._make_query(command, **args))
        )

        subscribed = True

        try:
            while True:
                event_data = self._receive_subscription_event(event_name)
                if event_data is None:
                    continue
                should_continue = callback(event_data)
                if should_continue is False:
                    break
        except ProcessingStoppedError:
            subscribed = False
            raise
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
