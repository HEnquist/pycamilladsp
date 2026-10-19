"""
Check the messages of the library against the websocket protocol schema of CamillaDSP.

Every public method is called against a fake websocket.
Each command the library sends is validated against `WsCommand`,
and each reply it is given is validated against `WsReply`,
so the replies the library is tested with are ones CamillaDSP can actually send.

`websocket_schema.json` is a copy of `docs/websocket_schema.json` from the camilladsp repo.
Refresh it with:

    gh api "repos/HEnquist/camilladsp/contents/docs/websocket_schema.json?ref=<tag>" \
        -H "Accept: application/vnd.github.raw" > tests/websocket_schema.json
"""

import inspect
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

import camilladsp
from test_camillaws import DummyWS

SCHEMA = json.loads((Path(__file__).parent / "websocket_schema.json").read_text())


def _validator(message_type):
    root = {**SCHEMA, "$ref": f"#/components/schemas/{message_type}"}
    return Draft202012Validator(root)


COMMAND_VALIDATOR = _validator("WsCommand")
REPLY_VALIDATOR = _validator("WsReply")


def _tags(message_type, field):
    variants = SCHEMA["components"]["schemas"][message_type]["oneOf"]
    names = set()
    for variant in variants:
        parts = variant.get("allOf", [variant])
        for part in parts:
            prop = part.get("properties", {}).get(field)
            if prop is not None:
                names.update(prop["enum"])
    return names


COMMAND_NAMES = _tags("WsCommand", "command")
REPLY_NAMES = _tags("WsReply", "reply")


def assert_valid(validator, message):
    error = best_match(validator.iter_errors(message))
    assert error is None, (
        f"{json.dumps(message)}\n{error.json_path}: {error.message}" if error else None
    )


CAPABILITIES = {
    "name": "hw:Loopback,0,0",
    "description": "Loopback, Loopback PCM, subdevice #0",
    "capability_sets": [
        {
            "mode": "Unified",
            "capabilities": [
                {
                    "channels": 2,
                    "samplerates": [
                        {"samplerate": 44100, "formats": ["S16_LE", "S32_LE"]}
                    ],
                }
            ],
        }
    ],
}
ALL_LEVELS = {
    "playback_rms": [-20.0, -21.0],
    "playback_peak": [-10.0, -11.0],
    "capture_rms": [-30.0, -31.0],
    "capture_peak": [-12.0, -13.0],
}
SPECTRUM = {"frequencies": [20.0, 44.7, 100.0], "magnitudes": [-42.3, -45.1, -38.7]}

# The value of a successful reply to each command. Commands missing here get a reply without
# a value.
REPLY_VALUES = {
    "GetVersion": "5.0.0",
    "GetSupportedDeviceTypes": [["Alsa", "File"], ["Alsa", "RawFile"]],
    "GetUpdateInterval": 100,
    "GetState": "Running",
    "GetStopReason": {"CaptureFormatChange": 44100},
    "GetCaptureRate": 44100,
    "GetSignalRange": 1.5,
    "GetRateAdjust": 1.0001,
    "GetBufferLevel": 1024,
    "GetClippedSamples": 3,
    "GetProcessingLoad": 12.5,
    "GetResamplerLoad": 4.5,
    "GetStateFilePath": "/path/to/statefile.yml",
    "GetStateFileUpdated": True,
    "GetCaptureSignalRms": [-30.0, -31.0],
    "GetCaptureSignalRmsSince": [-30.0, -31.0],
    "GetCaptureSignalRmsSinceLast": [-30.0, -31.0],
    "GetCaptureSignalPeak": [-12.0, -13.0],
    "GetCaptureSignalPeakSince": [-12.0, -13.0],
    "GetCaptureSignalPeakSinceLast": [-12.0, -13.0],
    "GetPlaybackSignalRms": [-20.0, -21.0],
    "GetPlaybackSignalRmsSince": [-20.0, -21.0],
    "GetPlaybackSignalRmsSinceLast": [-20.0, -21.0],
    "GetPlaybackSignalPeak": [-10.0, -11.0],
    "GetPlaybackSignalPeakSince": [-10.0, -11.0],
    "GetPlaybackSignalPeakSinceLast": [-10.0, -11.0],
    "GetSignalLevels": ALL_LEVELS,
    "GetSignalLevelsSince": ALL_LEVELS,
    "GetSignalLevelsSinceLast": ALL_LEVELS,
    "GetSignalPeaksSinceStart": {"playback": [-1.0, -2.0], "capture": [-3.0, -4.0]},
    "GetChannelLabels": {"playback": ["L", None], "capture": None},
    "GetSpectrum": SPECTRUM,
    "GetVolume": -12.0,
    "AdjustVolume": -15.0,
    "GetMute": False,
    "ToggleMute": True,
    "GetFaders": [{"volume": -12.0, "mute": False}] * 5,
    "GetFaderVolume": [1, -12.0],
    "AdjustFaderVolume": [1, -15.0],
    "GetFaderMute": [1, False],
    "ToggleFaderMute": [1, True],
    "GetConfig": "devices:\n  samplerate: 44100\n",
    "GetConfigJson": '{"devices": {"samplerate": 44100}}',
    "GetConfigTitle": "A title",
    "GetConfigDescription": "A description",
    "GetConfigFilePath": "/path/to/config.yml",
    "GetPreviousConfig": "devices:\n  samplerate: 48000\n",
    "GetConfigValue": 44100,
    "ReadConfig": "devices:\n  samplerate: 44100\n",
    "ReadConfigJson": '{"devices": {"samplerate": 44100}}',
    "ReadConfigFile": "devices:\n  samplerate: 44100\n",
    "ValidateConfig": "devices:\n  samplerate: 44100\n",
    "ValidateConfigJson": '{"devices": {"samplerate": 44100}}',
    "GetAvailableCaptureDevices": [["hw:Loopback,1,0", "Loopback capture"]],
    "GetAvailablePlaybackDevices": [["hw:Loopback,0,0", "Loopback playback"]],
    "GetCaptureDeviceCapabilities": CAPABILITIES,
    "GetPlaybackDeviceCapabilities": CAPABILITIES,
}

# The event each subscription pushes, as (event name, value).
SUBSCRIPTION_EVENTS = {
    "SubscribeState": ("StateEvent", {"state": "Inactive", "stop_reason": "Done"}),
    "SubscribeSignalLevels": (
        "SignalLevelsEvent",
        {"side": "capture", "rms": [-30.0, -31.0], "peak": [-12.0, -13.0]},
    ),
    "SubscribeVuLevels": ("VuLevelsEvent", ALL_LEVELS),
    "SubscribeSpectrum": ("SpectrumEvent", SPECTRUM),
}

# Every public method, called as (group, method, args, kwargs).
CALLS = [
    ("general", "state", (), {}),
    ("general", "subscribe_state", (), {}),
    ("general", "stop_reason", (), {}),
    ("general", "stop", (), {}),
    ("general", "exit", (), {}),
    ("general", "reload", (), {}),
    ("general", "supported_device_types", (), {}),
    ("general", "state_file_path", (), {}),
    ("general", "state_file_updated", (), {}),
    ("general", "list_playback_devices", ("Alsa",), {}),
    ("general", "list_capture_devices", ("Alsa",), {}),
    ("general", "playback_device_capabilities", ("Alsa", "hw:Loopback,0,0"), {}),
    ("general", "capture_device_capabilities", ("Alsa", "hw:Loopback,1,0"), {}),
    ("levels", "range", (), {}),
    ("levels", "range_decibel", (), {}),
    ("levels", "capture_rms", (), {}),
    ("levels", "playback_rms", (), {}),
    ("levels", "capture_peak", (), {}),
    ("levels", "playback_peak", (), {}),
    ("levels", "playback_peak_since", (2.5,), {}),
    ("levels", "playback_rms_since", (2,), {}),
    ("levels", "capture_peak_since", (2.5,), {}),
    ("levels", "capture_rms_since", (2,), {}),
    ("levels", "playback_peak_since_last", (), {}),
    ("levels", "playback_rms_since_last", (), {}),
    ("levels", "capture_peak_since_last", (), {}),
    ("levels", "capture_rms_since_last", (), {}),
    ("levels", "levels", (), {}),
    ("levels", "levels_since", (2,), {}),
    ("levels", "levels_since_last", (), {}),
    ("levels", "peaks_since_start", (), {}),
    ("levels", "reset_peaks_since_start", (), {}),
    ("levels", "labels", (), {}),
    ("levels", "subscribe_signal_levels", (), {"side": "capture"}),
    (
        "levels",
        "subscribe_vu_levels",
        (),
        {"max_rate": 30, "attack": 10, "release": 200},
    ),
    ("spectrum", "get_spectrum", ("capture", 20, 20000, 100), {}),
    ("spectrum", "get_spectrum", ("playback", 20.0, 20000.0, 100), {"channel": 1}),
    ("spectrum", "subscribe_spectrum", ("capture", 20, 20000, 100), {}),
    (
        "spectrum",
        "subscribe_spectrum",
        ("playback", 20.0, 20000.0, 100),
        {"channel": 0, "max_rate": 10},
    ),
    ("status", "rate_adjust", (), {}),
    ("status", "buffer_level", (), {}),
    ("status", "clipped_samples", (), {}),
    ("status", "reset_clipped_samples", (), {}),
    ("status", "processing_load", (), {}),
    ("status", "resampler_load", (), {}),
    ("settings", "update_interval", (), {}),
    ("settings", "set_update_interval", (500,), {}),
    ("rate", "capture_raw", (), {}),
    ("rate", "capture", (), {}),
    ("config", "file_path", (), {}),
    ("config", "set_file_path", ("/path/to/config.yml",), {}),
    ("config", "active_raw", (), {}),
    ("config", "set_active_raw", ("devices:\n  samplerate: 44100\n",), {}),
    ("config", "active_json", (), {}),
    ("config", "set_active_json", ('{"devices": {}}',), {}),
    ("config", "active", (), {}),
    ("config", "previous", (), {}),
    ("config", "parse_yaml", ("devices:\n  samplerate: 44100\n",), {}),
    ("config", "parse_json", ('{"devices": {}}',), {}),
    ("config", "read_and_parse_file", ("/path/to/config.yml",), {}),
    ("config", "set_active", ({"devices": {"samplerate": 44100}},), {}),
    ("config", "validate_json", ('{"devices": {}}',), {}),
    ("config", "validate_yaml", ("devices:\n  samplerate: 44100\n",), {}),
    ("config", "validate", ({"devices": {"samplerate": 44100}},), {}),
    ("config", "title", (), {}),
    ("config", "description", (), {}),
    ("config", "get_value", ("/devices/samplerate",), {}),
    ("config", "set_value", ("/devices/samplerate", 48000), {}),
    ("config", "patch", ({"devices": {"samplerate": 48000}},), {}),
    ("volume", "all", (), {}),
    ("volume", "main_volume", (), {}),
    ("volume", "set_main_volume", (-12,), {}),
    ("volume", "adjust_main_volume", (-3,), {}),
    ("volume", "adjust_main_volume", (-3,), {"min_limit": -50}),
    ("volume", "volume", (1,), {}),
    ("volume", "set_volume", (1, -12), {}),
    ("volume", "set_volume_external", (1, -12), {}),
    ("volume", "adjust_volume", (1, -3), {}),
    ("volume", "adjust_volume", (1, 3), {"max_limit": 0}),
    ("volume", "main_mute", (), {}),
    ("volume", "set_main_mute", (True,), {}),
    ("volume", "toggle_main_mute", (), {}),
    ("volume", "mute", (1,), {}),
    ("volume", "set_mute", (1, True), {}),
    ("volume", "toggle_mute", (1,), {}),
]

# Public methods that do not send anything.
NO_MESSAGE = {("versions", "camilladsp"), ("versions", "library")}

# Replies that report an error, with the exception the library should raise for each.
ERROR_REPLIES = [
    (
        "SetConfig",
        {
            "reply": "SetConfig",
            "result": "ConfigValidationError",
            "message": "filters.lp.parameters.freq: Frequency must be > 0",
        },
        camilladsp.ConfigValidationError,
    ),
    (
        "SetFaderVolume",
        {"reply": "SetFaderVolume", "result": "InvalidFaderError"},
        camilladsp.InvalidFaderError,
    ),
    (
        "GetSpectrum",
        {
            "reply": "GetSpectrum",
            "result": "InvalidRequestError",
            "message": "Insufficient data in buffer",
        },
        camilladsp.InvalidRequestError,
    ),
    (
        "StopSubscription",
        {"reply": "Invalid", "error": "No active subscription"},
        camilladsp.CamillaError,
    ),
]


class SchemaWS:
    """
    A fake websocket that checks each command against the schema,
    and answers with a reply that is also checked against the schema.
    """

    def __init__(self):
        self.commands = []
        self.replies = []
        self.pending = []

    def send(self, raw):
        command = json.loads(raw)
        assert_valid(COMMAND_VALIDATOR, command)
        name = command["command"]
        self.commands.append(name)
        reply = {"reply": name, "result": "Ok"}
        if name in REPLY_VALUES:
            reply["value"] = REPLY_VALUES[name]
        self.pending.append(reply)
        if name in SUBSCRIPTION_EVENTS:
            event, value = SUBSCRIPTION_EVENTS[name]
            self.pending.append({"reply": event, "result": "Ok", "value": value})

    def recv(self):
        reply = self.pending.pop(0)
        assert_valid(REPLY_VALIDATOR, reply)
        self.replies.append(reply["reply"])
        return json.dumps(reply)


def connected_client():
    """A client connected to a `SchemaWS`, which is available as `client.fake`."""
    fake = SchemaWS()
    connection = MagicMock()
    connection.send = MagicMock(side_effect=fake.send)
    connection.recv = MagicMock(side_effect=fake.recv)
    with patch(
        "camilladsp.camillaws.create_connection", MagicMock(return_value=connection)
    ):
        cdsp = camilladsp.CamillaClient("localhost", 1234)
        cdsp.connect()
    cdsp.fake = fake
    return cdsp


def run_call(group, method, args, kwargs):
    """Call a method of the library and return the `SchemaWS` it talked to."""
    client = connected_client()
    func = getattr(getattr(client, group), method)
    if method.startswith("subscribe_"):
        callback = MagicMock(return_value=False)
        func(callback, *args, **kwargs)
        callback.assert_called_once()
    else:
        func(*args, **kwargs)
    return client.fake


@pytest.mark.parametrize(
    "group, method, args, kwargs",
    CALLS,
    ids=[f"{group}.{method}" for group, method, _, _ in CALLS],
)
def test_messages_match_schema(group, method, args, kwargs):
    fake = run_call(group, method, args, kwargs)
    # The first command is the GetVersion sent by connect().
    assert len(fake.commands) > 1, "nothing was sent"
    assert not fake.pending, "not all replies were read"


@pytest.mark.parametrize(
    "command, reply, error",
    ERROR_REPLIES,
    ids=[
        f"{command}-{reply.get('result', reply['reply'])}"
        for command, reply, _ in ERROR_REPLIES
    ],
)
def test_error_replies(command, reply, error):
    assert_valid(REPLY_VALIDATOR, reply)
    client = connected_client()
    with patch.object(client, "_send_and_receive", return_value=json.dumps(reply)):
        with pytest.raises(error) as exc:
            client.query(command)
    assert exc.value.message == reply.get("message", reply.get("error"))


@pytest.mark.parametrize(
    "validator, message",
    [
        (COMMAND_VALIDATOR, {"command": "NoSuchCommand"}),
        (COMMAND_VALIDATOR, {"command": "SetVolume"}),
        (COMMAND_VALIDATOR, {"command": "SetVolume", "value": "-12"}),
        (COMMAND_VALIDATOR, {"command": "AdjustVolume", "value": -3, "maxvol": 0}),
        (
            COMMAND_VALIDATOR,
            {
                "command": "SubscribeSpectrum",
                "value": {
                    "side": "capture",
                    "min_freq": 20,
                    "max_freq": 20000,
                    "n_bins": 100,
                    "maxrate": 10,
                },
            },
        ),
        (REPLY_VALIDATOR, {"reply": "GetVolume", "result": "Ok", "value": "-12"}),
        (REPLY_VALIDATOR, {"reply": "GetVolume", "result": "NoSuchError"}),
        (
            REPLY_VALIDATOR,
            {
                "reply": "GetPlaybackDeviceCapabilities",
                "result": "Ok",
                "value": {
                    "name": "hw:0",
                    "description": "Card",
                    "capabilities": [{"channels": 2, "samplerates": []}],
                },
            },
        ),
    ],
)
def test_schema_rejects_invalid_messages(validator, message):
    """Make sure the schema checks above would actually catch a mistake."""
    with pytest.raises(AssertionError):
        assert_valid(validator, message)


def test_dummy_replies_match_schema():
    """The canned replies in test_camillaws.py that use real reply names."""
    checked = 0
    for raw in DummyWS.responses.values():
        try:
            message = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if message.get("reply") in REPLY_NAMES:
            assert_valid(REPLY_VALIDATOR, message)
            checked += 1
    assert checked > 0


def test_every_public_method_is_called():
    client = camilladsp.CamillaClient("localhost", 1234)
    called = {(group, method) for group, method, _, _ in CALLS}
    groups = [
        name
        for name, value in inspect.getmembers(type(client))
        if isinstance(value, property)
    ]
    for group in groups:
        for method, _ in inspect.getmembers(
            getattr(client, group), predicate=inspect.ismethod
        ):
            if method.startswith("_"):
                continue
            assert (group, method) in called | NO_MESSAGE, f"{group}.{method}"


def test_every_message_is_covered():
    commands = set()
    replies = {reply["reply"] for _, reply, _ in ERROR_REPLIES}
    for call in CALLS:
        fake = run_call(*call)
        commands.update(fake.commands)
        replies.update(fake.replies)
    assert COMMAND_NAMES - commands == set()
    assert REPLY_NAMES - replies == set()
