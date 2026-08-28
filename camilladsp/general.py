"""
Python library for communicating with CamillaDSP.

This module contains commands of general nature.
"""

from typing import Any, Callable, List, Optional, Tuple

from .commandgroup import _CommandGroup
from .datastructures import (
    AudioDeviceDescriptor,
    ProcessingState,
    StopReason,
    _state_from_string,
    _reason_from_reply,
)


class General(_CommandGroup):
    """
    Basic commands
    """

    # ========================= CamillaDSP state =========================

    def state(self) -> Optional[ProcessingState]:
        """
        Get current processing state.

        Returns:
            ProcessingState | None: Current processing state.
        """
        state = self.client.query("GetState")
        return _state_from_string(state)

    def subscribe_state(self, callback: Callable[[Any], Optional[bool]]):
        """
        Subscribe to state change events and call `callback` for each event.

        This method blocks until `callback` returns `False`.

        Args:
            callback: Function that receives event payloads.
                Typical payload keys are `state` and `stop_reason`.
        """
        self.client.subscribe_events(
            command="SubscribeState",
            event_name="StateEvent",
            callback=callback,
        )

    def stop_reason(self) -> StopReason:
        """
        Get reason why processing stopped.

        Returns:
            StopReason: Stop reason enum variant.
        """
        reason = self.client.query("GetStopReason")
        return _reason_from_reply(reason)

    # ========================= Basic commands =========================

    def stop(self):
        """
        Stop processing and wait for new config if wait mode is active, else exit.
        """
        self.client.query("Stop")

    def exit(self):
        """
        Stop processing and exit.
        """
        self.client.query("Exit")

    def reload(self):
        """
        Reload config from disk.
        """
        self.client.query("Reload")

    def supported_device_types(self) -> Tuple[List[str], List[str]]:
        """
        Read what device types the running CamillaDSP process supports.
        Returns a tuple with two lists of device types,
        the first for playback and the second for capture.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing two lists,
                with the supported playback and capture device types.
        """
        playback, capture = self.client.query("GetSupportedDeviceTypes")
        return (playback, capture)

    def state_file_path(self) -> Optional[str]:
        """
        Get path to current state file.

        Returns:
            str | None: Path to state file, or None.
        """
        path = self.client.query("GetStateFilePath")
        return path

    def state_file_updated(self) -> bool:
        """
        Check if all changes have been saved to the state file.

        Returns:
            bool: True if all changes are saved.
        """
        updated = self.client.query("GetStateFileUpdated")
        return updated

    def list_playback_devices(self, value: str) -> List[Tuple[str, str]]:
        """
        List the available playback devices for a given backend.
        Returns a list of tuples. Returns the system name and
        a descriptive name for each device.
        For some backends, those two names are identical.

        Returns:
            List[Tuple[str, str]]: A list containing tuples of two strings,
                with system device name and a descriptive name.
        """
        devs = self.client.query("GetAvailablePlaybackDevices", backend=value)
        return devs

    def list_capture_devices(self, value: str) -> List[Tuple[str, str]]:
        """
        List the available capture devices for a given backend.
        Returns a list of tuples. Returns the system name and
        a descriptive name for each device.
        For some backends, those two names are identical.

        Returns:
            List[Tuple[str, str]]: A list containing tuples of two strings,
                with system device name and a descriptive name.
        """
        devs = self.client.query("GetAvailableCaptureDevices", backend=value)
        return devs

    def playback_device_capabilities(
        self, backend: str, device_name: str
    ) -> AudioDeviceDescriptor:
        """
        Read the capabilities of a specific playback device.

        Args:
            backend (str): Backend name such as Alsa or CoreAudio.
            device_name (str): Device identifier or name.

        Returns:
            AudioDeviceDescriptor: Device descriptor with capabilities.
        """
        capabilities = self.client.query(
            "GetPlaybackDeviceCapabilities", backend=backend, device=device_name
        )
        return capabilities

    def capture_device_capabilities(
        self, backend: str, device_name: str
    ) -> AudioDeviceDescriptor:
        """
        Read the capabilities of a specific capture device.

        Args:
            backend (str): Backend name such as Alsa or CoreAudio.
            device_name (str): Device identifier or name.

        Returns:
            AudioDeviceDescriptor: Device descriptor with capabilities.
        """
        capabilities = self.client.query(
            "GetCaptureDeviceCapabilities", backend=backend, device=device_name
        )
        return capabilities
