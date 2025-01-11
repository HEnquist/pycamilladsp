"""
Python library for communicating with CamillaDSP.

The main component is the `CamillaClient` class.
This class handles the communication over websocket with the CamillaDSP process.

The various commands are grouped on helper classes that are instantiated
by the CamillaClient class.
For example volume controls are handled by the `Volume` class.
These methods are accessible via the `volume` property of the CamillaClient.
Reading the main volume is then done by calling `my_client.volume.main()`.
"""

from .camillaws import _CamillaWS
from .volume import Volume
from .levels import Levels
from .ratemonitor import RateMonitor
from .general import General
from .config import Config
from .settings import Settings
from .status import Status
from .versions import Versions


class CamillaClient(_CamillaWS):
    """
    Class for communicating with CamillaDSP.

    Args:
        host (str): Hostname where CamillaDSP runs.
        port (int): Port number of the CamillaDSP websocket server.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, host: str, port: int):
        """
        Create a new CamillaClient.

        The newly created CamillaClient does not
        automatically connect to the CamillaDSP process.
        Call `connect()` to initiate the connection.

        Args:
            host (str): Hostname where CamillaDSP runs.
            port (int): Port number of the CamillaDSP websocket server.
        """
        super().__init__(host, port)

        self._volume = Volume(self)
        self._rate = RateMonitor(self)
        self._levels = Levels(self)
        self._config = Config(self)
        self._status = Status(self)
        self._settings = Settings(self)
        self._general = General(self)
        self._versions = Versions(self)

    @property
    def volume(self) -> Volume:
        """
        A `Volume` instance for volume and mute controls.
        """
        return self._volume

    @property
    def rate(self) -> RateMonitor:
        """
        A `RateMonitor` instance for rate monitoring commands.
        """
        return self._rate

    @property
    def levels(self) -> Levels:
        """
        A `Levels` instance for signal level monitoring.
        """
        return self._levels

    @property
    def config(self) -> Config:
        """
        A `Config` instance for config management commands.
        """
        return self._config

    @property
    def status(self) -> Status:
        """
        A `Status` instance for status commands.
        """
        return self._status

    @property
    def settings(self) -> Settings:
        """
        A `Settings` instance for reading and writing settings.
        """
        return self._settings

    @property
    def general(self) -> General:
        """
        A `General` instance for basic commands.
        """
        return self._general

    @property
    def versions(self) -> Versions:
        """
        A `Versions` instance for version info.
        """
        return self._versions
