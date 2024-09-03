"""
Python library for communicating with CamillaDSP.

This module contains the websocket connection class.
"""

from typing import Tuple, Optional, Union
from threading import Lock
import json
from websocket import create_connection, WebSocket  # type: ignore

from .datastructures import CamillaError


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
        if arg is not None:
            query = json.dumps({command: arg})
        else:
            query = json.dumps(command)
        try:
            with self._lock:
                self._ws.send(query)
                rawrepl = self._ws.recv()
        except Exception as err:
            self._ws = None
            raise IOError("Lost connection to CamillaDSP") from err
        return self._handle_reply(command, rawrepl)

    def _handle_reply(self, command: str, rawreply: Union[str, bytes]):
        try:
            reply = json.loads(rawreply)
            value = None
            if command in reply:
                state = reply[command]["result"]
                if "value" in reply[command]:
                    value = reply[command]["value"]
                if state == "Error" and value is not None:
                    raise CamillaError(value)
                if state == "Error" and value is None:
                    raise CamillaError("Command returned an error")
                if state == "Ok" and value is not None:
                    return value
                return None
            raise IOError(f"Invalid response received: {rawreply!r}")
        except json.JSONDecodeError as err:
            raise IOError(f"Invalid response received: {rawreply!r}") from err

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
