from camilladsp import StopReason
import pytest
from unittest.mock import MagicMock, patch
import camilladsp
import json


def cmd(name, **args):
    """Build a command string in the same way the library does."""
    return json.dumps({"command": name, **args})


def reply(name, **fields):
    """Build a reply message as sent by CamillaDSP."""
    return json.dumps({"reply": name, **fields})


class DummyWS:
    def __init__(self):
        self.query = None
        self.response = None
        self.value = None

    responses = {
        cmd("GetState"): reply("GetState", result="Ok", value="Inactive"),
        cmd("GetVersion"): reply("GetVersion", result="Ok", value="0.3.2"),
        cmd("GetSupportedDeviceTypes"): reply(
            "GetSupportedDeviceTypes", result="Ok", value=[["a", "b"], ["c", "d"]]
        ),
        cmd("GetSignalRange"): reply("GetSignalRange", result="Ok", value="0.2"),
        cmd("GetCaptureSignalRms"): reply(
            "GetCaptureSignalRms", result="Ok", value=[0.1, 0.2]
        ),
        cmd("GetCaptureRate"): reply("GetCaptureRate", result="Ok", value="88250"),
        cmd("GetFaders"): reply(
            "GetFaders",
            result="Ok",
            value=[
                {"volume": -1, "mute": False},
                {"volume": -2, "mute": True},
                {"volume": -3, "mute": False},
                {"volume": -4, "mute": True},
                {"volume": -5, "mute": False},
            ],
        ),
        cmd("GetFaderVolume", fader=1): reply(
            "GetFaderVolume", result="Ok", value=[1, -1.23]
        ),
        cmd("AdjustFaderVolume", fader=1, value=-2.5): reply(
            "AdjustFaderVolume", result="Ok", value=[1, -3.73]
        ),
        cmd("AdjustVolume", value=-2.5): reply(
            "AdjustVolume", result="Ok", value=-3.73
        ),
        cmd("GetFaderMute", fader=1): reply(
            "GetFaderMute", result="Ok", value=[1, False]
        ),
        cmd("ToggleFaderMute", fader=1): reply(
            "ToggleFaderMute", result="Ok", value=[1, True]
        ),
        cmd("ToggleMute"): reply("ToggleMute", result="Ok", value=True),
        cmd(
            "GetPlaybackDeviceCapabilities",
            backend="Alsa",
            device="hw:Loopback,0,0",
        ): reply(
            "GetPlaybackDeviceCapabilities",
            result="Ok",
            value={
                "name": "hw:Loopback,0,0",
                "description": "Loopback, Loopback PCM, subdevice #0",
                "capabilities": [
                    {
                        "channels": 2,
                        "samplerates": [
                            {
                                "samplerate": 44100,
                                "formats": ["S16_LE", "S32_LE"],
                            }
                        ],
                    }
                ],
            },
        ),
        cmd(
            "GetCaptureDeviceCapabilities",
            backend="Alsa",
            device="hw:Loopback,1,0",
        ): reply(
            "GetCaptureDeviceCapabilities",
            result="Ok",
            value={
                "name": "hw:Loopback,1,0",
                "description": "Loopback capture",
                "capabilities": [
                    {
                        "channels": 2,
                        "samplerates": [
                            {"samplerate": 48000, "formats": ["FLOAT32LE"]}
                        ],
                    }
                ],
            },
        ),
        cmd("GetErrorValue"): reply("GetErrorValue", result="Error", value="badstuff"),
        cmd("GetError"): reply("GetError", result="Error"),
        cmd("InvalidValue"): reply(
            "InvalidValue",
            result="InvalidValueError",
            message="invalid value",
            value="badstuff",
        ),
        cmd("InvalidRequest"): reply(
            "InvalidRequest",
            result="InvalidRequestError",
            message="invalid request",
            value="badstuff",
        ),
        cmd("InvalidFader"): reply("InvalidFader", result="InvalidFaderError"),
        cmd("TooManyRequests"): reply(
            "TooManyRequests",
            result="RateLimitExceededError",
            message="too many requests",
        ),
        cmd("DeviceBusy"): reply(
            "DeviceBusy", result="DeviceBusyError", message="device is busy"
        ),
        cmd("DeviceNotFound"): reply(
            "DeviceNotFound", result="DeviceNotFoundError", message="device not found"
        ),
        cmd("DeviceError"): reply(
            "DeviceError", result="DeviceError", message="backend failed"
        ),
        cmd("GetStopReason"): reply("GetStopReason", result="Ok", value="Done"),
        cmd("GetStopReason2"): reply(
            "GetStopReason", result="Ok", value={"CaptureFormatChange": 44098}
        ),
        cmd("GetStopReason3"): reply(
            "GetStopReason", result="Ok", value={"CaptureError": "error error"}
        ),
        cmd("GetStopReason4"): reply(
            "GetStopReason", result="Ok", value={"UnknownError": "something broke"}
        ),
        cmd(
            "GetSpectrum",
            value={
                "side": "capture",
                "channel": None,
                "min_freq": 20.0,
                "max_freq": 20000.0,
                "n_bins": 100,
            },
        ): reply(
            "GetSpectrum",
            result="Ok",
            value={
                "frequencies": [20.0, 44.7, 100.0],
                "magnitudes": [-42.3, -45.1, -38.7],
            },
        ),
        cmd("NotACommand"): reply("Invalid", error="Some error"),
        cmd("WrongReply"): reply("SomeOtherCommand", result="Ok"),
        cmd("NoResult"): reply("NoResult", value=123),
        cmd("SetSomeValue", value=123): reply("SetSomeValue", result="Ok"),
        cmd("nonsense"): "abcdefgh",
        cmd("bug_in_ws"): "OK:OTHER",
    }

    def send(self, query):
        if query == cmd("fail"):
            raise IOError("not connected")
        self.query = query
        print(query)
        if query in self.responses:
            self.response = self.responses[query]
        else:
            self.response = reply("Invalid", error="Error")

    def recv(self):
        print(self.response)
        return self.response


@pytest.fixture
def camilla_mockws():
    connection = MagicMock()
    create_connection = MagicMock(return_value=connection)
    ws_dummy = DummyWS()
    connection.send = MagicMock(side_effect=ws_dummy.send)
    connection.recv = MagicMock(side_effect=ws_dummy.recv)
    with patch("camilladsp.camillaws.create_connection", create_connection):
        cdsp = camilladsp.camilladsp.CamillaClient("localhost", 1234)
        cdsp.dummyws = ws_dummy
        cdsp.mockconnection = connection
        yield cdsp


@pytest.fixture
def camilla():
    cdsp = camilladsp.camilladsp.CamillaClient("localhost", 12345)
    yield cdsp


@pytest.fixture
def camilla_mockquery():
    query_dummy = MagicMock()
    with patch("camilladsp.camilladsp.CamillaClient.query", query_dummy):
        cdsp = camilladsp.camilladsp.CamillaClient("localhost", 1234)
        yield cdsp


@pytest.fixture
def camilla_mockquery_yaml():
    query_dummy = MagicMock(return_value="some: value\n")
    with patch("camilladsp.camilladsp.CamillaClient.query", query_dummy):
        cdsp = camilladsp.camilladsp.CamillaClient("localhost", 1234)
        yield cdsp


def test_connect(camilla_mockws):
    with pytest.raises(IOError):
        camilla_mockws.general.state()
    camilla_mockws.connect()
    assert camilla_mockws.is_connected()
    assert camilla_mockws.general.state() == camilladsp.ProcessingState.INACTIVE
    assert camilla_mockws.versions.camilladsp() == ("0", "3", "2")
    assert camilla_mockws.versions.library() == tuple(camilladsp.VERSION.split("."))
    camilla_mockws.disconnect()
    assert not camilla_mockws.is_connected()


def test_connect_fail(camilla):
    with pytest.raises(IOError):
        camilla.connect()


def test_device_types(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.general.supported_device_types() == (["a", "b"], ["c", "d"])


def test_device_capabilities(camilla_mockws):
    camilla_mockws.connect()
    playback = camilla_mockws.general.playback_device_capabilities(
        "Alsa", "hw:Loopback,0,0"
    )
    capture = camilla_mockws.general.capture_device_capabilities(
        "Alsa", "hw:Loopback,1,0"
    )

    assert playback["name"] == "hw:Loopback,0,0"
    assert playback["capabilities"][0]["samplerates"][0]["formats"] == [
        "S16_LE",
        "S32_LE",
    ]
    assert capture["description"] == "Loopback capture"
    assert capture["capabilities"][0]["samplerates"][0]["samplerate"] == 48000


def test_signal_range(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.levels.range() == 0.2


def test_signal_rms(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.levels.capture_rms() == [0.1, 0.2]


def test_signal_range_decibel(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.levels.range_decibel() == -20
    camilla_mockws.dummyws.responses[cmd("GetSignalRange")] = reply(
        "GetSignalRange", result="Ok", value="0.0"
    )
    assert camilla_mockws.levels.range_decibel() == -1000


def test_disconnect_fail(camilla_mockws):
    camilla_mockws.connect()

    def raise_error():
        raise IOError("disconnected")

    camilla_mockws.mockconnection.close = MagicMock(side_effect=raise_error)
    camilla_mockws.disconnect()
    assert not camilla_mockws.is_connected()


def test_capture_rate(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.rate.capture() == 88200
    assert camilla_mockws.rate.capture_raw() == 88250


def test_stop_reason(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.general.stop_reason() == StopReason.DONE
    assert camilla_mockws.general.stop_reason().data == None
    print(camilla_mockws.dummyws.responses)
    camilla_mockws.dummyws.responses[cmd("GetStopReason")] = (
        camilla_mockws.dummyws.responses[cmd("GetStopReason2")]
    )
    assert camilla_mockws.general.stop_reason() == StopReason.CAPTUREFORMATCHANGE
    assert camilla_mockws.general.stop_reason().data == 44098
    camilla_mockws.dummyws.responses[cmd("GetStopReason")] = (
        camilla_mockws.dummyws.responses[cmd("GetStopReason3")]
    )
    assert camilla_mockws.general.stop_reason() == StopReason.CAPTUREERROR
    assert camilla_mockws.general.stop_reason().data == "error error"
    camilla_mockws.dummyws.responses[cmd("GetStopReason")] = (
        camilla_mockws.dummyws.responses[cmd("GetStopReason4")]
    )
    assert camilla_mockws.general.stop_reason() == StopReason.UNKNOWNERROR
    assert camilla_mockws.general.stop_reason().data == "something broke"


def test_query(camilla_mockws):
    camilla_mockws.connect()
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws.query("GetError")
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws.query("GetErrorValue")
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws.query("Invalid")
    with pytest.raises(IOError):
        camilla_mockws.query("bug_in_ws")
    with pytest.raises(IOError):
        camilla_mockws.query("fail")


def test_query_unknown_command(camilla_mockws):
    """An `Invalid` reply means CamillaDSP did not accept the command."""
    camilla_mockws.connect()
    with pytest.raises(camilladsp.CamillaError) as exc:
        camilla_mockws.query("NotACommand")
    assert exc.value.message == "Some error"


def test_query_mismatched_reply(camilla_mockws):
    camilla_mockws.connect()
    with pytest.raises(IOError):
        camilla_mockws.query("WrongReply")
    with pytest.raises(IOError):
        camilla_mockws.query("NoResult")


def test_query_invalid_value(camilla_mockws):
    camilla_mockws.connect()
    with pytest.raises(camilladsp.InvalidValueError) as exc:
        camilla_mockws.query("InvalidValue")
    exc_val = exc.value
    assert exc_val.message == "invalid value"
    assert exc_val.value == "badstuff"
    assert str(exc_val) == "invalid value"
    assert repr(exc_val) == "InvalidValueError('invalid value')"


def test_query_invalid_request(camilla_mockws):
    camilla_mockws.connect()
    with pytest.raises(camilladsp.InvalidRequestError) as exc:
        camilla_mockws.query("InvalidRequest")
    assert exc.value.message == "invalid request"
    assert exc.value.value == "badstuff"


def test_query_invalid_fader(camilla_mockws):
    camilla_mockws.connect()
    with pytest.raises(camilladsp.InvalidFaderError) as exc:
        camilla_mockws.query("InvalidFader")
    assert exc.value.message is None


def test_query_too_many_requests(camilla_mockws):
    camilla_mockws.connect()
    with pytest.raises(camilladsp.RateLimitExceededError) as exc:
        camilla_mockws.query("TooManyRequests")
    assert exc.value.message is None
    assert exc.value.value is None


def test_query_device_errors(camilla_mockws):
    camilla_mockws.connect()

    with pytest.raises(camilladsp.DeviceBusyError) as busy_exc:
        camilla_mockws.query("DeviceBusy")
    assert busy_exc.value.message == "device is busy"

    with pytest.raises(camilladsp.DeviceNotFoundError) as missing_exc:
        camilla_mockws.query("DeviceNotFound")
    assert missing_exc.value.message == "device not found"

    with pytest.raises(camilladsp.DeviceError) as device_exc:
        camilla_mockws.query("DeviceError")
    assert device_exc.value.message == "backend failed"


def test_query_mockedws(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.query("SetSomeValue", value=123) is None
    assert camilla_mockws.dummyws.query == cmd("SetSomeValue", value=123)
    assert camilla_mockws.general.supported_device_types() == (["a", "b"], ["c", "d"])
    assert camilla_mockws.volume.volume(1) == -1.23
    assert camilla_mockws.volume.adjust_volume(1, -2.5) == -3.73
    assert camilla_mockws.volume.adjust_main_volume(-2.5) == -3.73
    assert camilla_mockws.volume.mute(1) == False
    assert camilla_mockws.volume.toggle_mute(1) == True
    assert camilla_mockws.volume.toggle_main_mute() == True
    faders = camilla_mockws.volume.all()
    assert faders[0]["volume"] == -1.0
    assert faders[2]["volume"] == -3.0
    assert faders[0]["mute"] == False
    assert faders[1]["mute"] == True


def test_queries(camilla_mockquery):
    # rate
    camilla_mockquery.rate.capture()
    camilla_mockquery.query.assert_called_with("GetCaptureRate")
    camilla_mockquery.rate.capture_raw()
    camilla_mockquery.query.assert_called_with("GetCaptureRate")

    # levels
    camilla_mockquery.levels.range()
    camilla_mockquery.query.assert_called_with("GetSignalRange")
    camilla_mockquery.levels.range_decibel()
    camilla_mockquery.query.assert_called_with("GetSignalRange")
    camilla_mockquery.levels.capture_rms()
    camilla_mockquery.query.assert_called_with("GetCaptureSignalRms")
    camilla_mockquery.levels.capture_peak()
    camilla_mockquery.query.assert_called_with("GetCaptureSignalPeak")
    camilla_mockquery.levels.playback_rms()
    camilla_mockquery.query.assert_called_with("GetPlaybackSignalRms")
    camilla_mockquery.levels.playback_peak()
    camilla_mockquery.query.assert_called_with("GetPlaybackSignalPeak")
    camilla_mockquery.levels.capture_rms_since(2.5)
    camilla_mockquery.query.assert_called_with("GetCaptureSignalRmsSince", value=2.5)
    camilla_mockquery.levels.playback_peak_since(2.5)
    camilla_mockquery.query.assert_called_with("GetPlaybackSignalPeakSince", value=2.5)
    camilla_mockquery.levels.levels_since(2.5)
    camilla_mockquery.query.assert_called_with("GetSignalLevelsSince", value=2.5)
    camilla_mockquery.levels.labels()
    camilla_mockquery.query.assert_called_with("GetChannelLabels")

    # settings
    camilla_mockquery.settings.set_update_interval(1234)
    camilla_mockquery.query.assert_called_with("SetUpdateInterval", value=1234)
    camilla_mockquery.settings.update_interval()
    camilla_mockquery.query.assert_called_with("GetUpdateInterval")

    # general
    camilla_mockquery.general.stop()
    camilla_mockquery.query.assert_called_with("Stop")
    camilla_mockquery.general.exit()
    camilla_mockquery.query.assert_called_with("Exit")
    camilla_mockquery.general.reload()
    camilla_mockquery.query.assert_called_with("Reload")
    camilla_mockquery.general.list_playback_devices("Alsa")
    camilla_mockquery.query.assert_called_with(
        "GetAvailablePlaybackDevices", backend="Alsa"
    )
    camilla_mockquery.general.list_capture_devices("Alsa")
    camilla_mockquery.query.assert_called_with(
        "GetAvailableCaptureDevices", backend="Alsa"
    )
    camilla_mockquery.general.playback_device_capabilities("Alsa", "hw:Loopback,0,0")
    camilla_mockquery.query.assert_called_with(
        "GetPlaybackDeviceCapabilities", backend="Alsa", device="hw:Loopback,0,0"
    )
    camilla_mockquery.general.capture_device_capabilities("Alsa", "hw:Loopback,1,0")
    camilla_mockquery.query.assert_called_with(
        "GetCaptureDeviceCapabilities", backend="Alsa", device="hw:Loopback,1,0"
    )

    # config
    camilla_mockquery.config.file_path()
    camilla_mockquery.query.assert_called_with("GetConfigFilePath")
    camilla_mockquery.config.set_file_path("some/path")
    camilla_mockquery.query.assert_called_with("SetConfigFilePath", value="some/path")
    camilla_mockquery.config.active_raw()
    camilla_mockquery.query.assert_called_with("GetConfig")
    camilla_mockquery.config.active_json()
    camilla_mockquery.query.assert_called_with("GetConfigJson")
    camilla_mockquery.config.set_active_raw("some:yaml")
    camilla_mockquery.query.assert_called_with("SetConfig", value="some:yaml")
    camilla_mockquery.config.set_active_json("{'some': 'json'}")
    camilla_mockquery.query.assert_called_with(
        "SetConfigJson", value="{'some': 'json'}"
    )
    camilla_mockquery.config.set_active({"some": "yaml"})
    camilla_mockquery.query.assert_called_with("SetConfig", value="some: yaml\n")
    camilla_mockquery.config.get_value("some")
    camilla_mockquery.query.assert_called_with("GetConfigValue", value="some")
    camilla_mockquery.config.set_value("some", "value")
    camilla_mockquery.query.assert_called_with(
        "SetConfigValue", pointer="some", value="value"
    )
    camilla_mockquery.config.patch({"some": "value"})
    camilla_mockquery.query.assert_called_with("PatchConfig", value={"some": "value"})

    # status
    camilla_mockquery.status.rate_adjust()
    camilla_mockquery.query.assert_called_with("GetRateAdjust")
    camilla_mockquery.status.buffer_level()
    camilla_mockquery.query.assert_called_with("GetBufferLevel")
    camilla_mockquery.status.clipped_samples()
    camilla_mockquery.query.assert_called_with("GetClippedSamples")
    camilla_mockquery.status.reset_clipped_samples()
    camilla_mockquery.query.assert_called_with("ResetClippedSamples")
    camilla_mockquery.status.processing_load()
    camilla_mockquery.query.assert_called_with("GetProcessingLoad")
    camilla_mockquery.status.resampler_load()
    camilla_mockquery.query.assert_called_with("GetResamplerLoad")

    # volume & mute
    camilla_mockquery.volume.main_volume()
    camilla_mockquery.query.assert_called_with("GetVolume")
    camilla_mockquery.volume.set_main_volume(-25.0)
    camilla_mockquery.query.assert_called_with("SetVolume", value=-25.0)
    camilla_mockquery.volume.set_volume(1, -1.23)
    camilla_mockquery.query.assert_called_with("SetFaderVolume", fader=1, value=-1.23)
    camilla_mockquery.volume.set_volume_external(1, -1.23)
    camilla_mockquery.query.assert_called_with(
        "SetFaderExternalVolume", fader=1, value=-1.23
    )
    camilla_mockquery.volume.main_mute()
    camilla_mockquery.query.assert_called_with("GetMute")
    camilla_mockquery.volume.set_main_mute(False)
    camilla_mockquery.query.assert_called_with("SetMute", value=False)
    camilla_mockquery.volume.set_mute(1, False)
    camilla_mockquery.query.assert_called_with("SetFaderMute", fader=1, value=False)


def test_queries_adv(camilla_mockquery_yaml):
    camilla_mockquery_yaml.config.read_and_parse_file("some/path")
    camilla_mockquery_yaml.query.assert_called_with("ReadConfigFile", value="some/path")
    camilla_mockquery_yaml.config.parse_yaml("rawyaml")
    camilla_mockquery_yaml.query.assert_called_with("ReadConfig", value="rawyaml")
    camilla_mockquery_yaml.config.validate({"some": "yaml"})
    camilla_mockquery_yaml.query.assert_called_with(
        "ValidateConfig", value="some: yaml\n"
    )
    camilla_mockquery_yaml.config.active()
    camilla_mockquery_yaml.query.assert_called_with("GetConfig")
    camilla_mockquery_yaml.config.previous()
    camilla_mockquery_yaml.query.assert_called_with("GetPreviousConfig")


def test_queries_customreplies(camilla_mockquery):
    camilla_mockquery.query.return_value = [0, -12.0]
    camilla_mockquery.volume.adjust_volume(0, -5.0)
    camilla_mockquery.query.assert_called_with("AdjustFaderVolume", fader=0, value=-5.0)
    camilla_mockquery.volume.adjust_volume(0, -5.0, min_limit=-20, max_limit=3.0)
    camilla_mockquery.query.assert_called_with(
        "AdjustFaderVolume", fader=0, value=-5.0, min=-20.0, max=3.0
    )
    camilla_mockquery.volume.adjust_volume(0, -5.0, min_limit=-20)
    camilla_mockquery.query.assert_called_with(
        "AdjustFaderVolume", fader=0, value=-5.0, min=-20.0, max=50.0
    )
    camilla_mockquery.volume.adjust_volume(0, -5.0, max_limit=3.0)
    camilla_mockquery.query.assert_called_with(
        "AdjustFaderVolume", fader=0, value=-5.0, min=-150.0, max=3.0
    )

    camilla_mockquery.query.return_value = -12.0
    camilla_mockquery.volume.adjust_main_volume(-5.0)
    camilla_mockquery.query.assert_called_with("AdjustVolume", value=-5.0)
    camilla_mockquery.volume.adjust_main_volume(-5.0, min_limit=-20, max_limit=3.0)
    camilla_mockquery.query.assert_called_with(
        "AdjustVolume", value=-5.0, min=-20.0, max=3.0
    )


def test_subscribe_signal_levels(camilla_mockquery):
    callback = MagicMock(return_value=False)
    camilla_mockquery.subscribe_events = MagicMock()

    camilla_mockquery.levels.subscribe_signal_levels(callback, side="playback")

    camilla_mockquery.subscribe_events.assert_called_with(
        command="SubscribeSignalLevels",
        event_name="SignalLevelsEvent",
        callback=callback,
        value="playback",
    )


def test_subscribe_state(camilla_mockquery):
    callback = MagicMock(return_value=False)
    camilla_mockquery.subscribe_events = MagicMock()

    camilla_mockquery.general.subscribe_state(callback)

    camilla_mockquery.subscribe_events.assert_called_with(
        command="SubscribeState",
        event_name="StateEvent",
        callback=callback,
    )


def test_subscribe_vu_levels(camilla_mockquery):
    callback = MagicMock(return_value=False)
    camilla_mockquery.subscribe_events = MagicMock()

    camilla_mockquery.levels.subscribe_vu_levels(
        callback, max_rate=30, attack=10, release=200
    )

    camilla_mockquery.subscribe_events.assert_called_with(
        command="SubscribeVuLevels",
        event_name="VuLevelsEvent",
        callback=callback,
        value={"max_rate": 30.0, "attack": 10.0, "release": 200.0},
    )


def test_subscribe_events(camilla_mockws):
    camilla_mockws.connect()
    sent = []
    replies = iter(
        [
            reply("SubscribeSignalLevels", result="Ok"),
            reply(
                "SignalLevelsEvent",
                result="Ok",
                value={
                    "side": "capture",
                    "rms": [-58.1, -57.6],
                    "peak": [-39.4, -38.9],
                },
            ),
            reply("StopSubscription", result="Ok"),
        ]
    )

    camilla_mockws.mockconnection.send = MagicMock(
        side_effect=lambda msg: sent.append(msg)
    )
    camilla_mockws.mockconnection.recv = MagicMock(side_effect=lambda: next(replies))

    events = []

    def on_event(event_data):
        events.append(event_data)
        return False

    camilla_mockws.subscribe_events(
        command="SubscribeSignalLevels",
        event_name="SignalLevelsEvent",
        callback=on_event,
        value="capture",
    )

    assert sent == [
        cmd("SubscribeSignalLevels", value="capture"),
        cmd("StopSubscription"),
    ]
    assert events == [
        {
            "side": "capture",
            "rms": [-58.1, -57.6],
            "peak": [-39.4, -38.9],
        }
    ]


def test_subscribe_vu_events(camilla_mockws):
    camilla_mockws.connect()
    sent = []
    replies = iter(
        [
            reply("SubscribeVuLevels", result="Ok"),
            reply(
                "VuLevelsEvent",
                result="Ok",
                value={
                    "playback_rms": [-20.0, -21.0],
                    "playback_peak": [-10.0, -11.0],
                    "capture_rms": [-30.0, -31.0],
                    "capture_peak": [-12.0, -13.0],
                },
            ),
            reply("StopSubscription", result="Ok"),
        ]
    )

    camilla_mockws.mockconnection.send = MagicMock(
        side_effect=lambda msg: sent.append(msg)
    )
    camilla_mockws.mockconnection.recv = MagicMock(side_effect=lambda: next(replies))

    events = []

    def on_event(event_data):
        events.append(event_data)
        return False

    camilla_mockws.levels.subscribe_vu_levels(
        on_event, max_rate=30, attack=10, release=200
    )

    assert events == [
        {
            "playback_rms": [-20.0, -21.0],
            "playback_peak": [-10.0, -11.0],
            "capture_rms": [-30.0, -31.0],
            "capture_peak": [-12.0, -13.0],
        }
    ]
    assert sent == [
        cmd(
            "SubscribeVuLevels",
            value={"max_rate": 30.0, "attack": 10.0, "release": 200.0},
        ),
        cmd("StopSubscription"),
    ]


def test_get_spectrum(camilla_mockws):
    camilla_mockws.connect()
    result = camilla_mockws.spectrum.get_spectrum(
        side="capture", min_freq=20.0, max_freq=20000.0, n_bins=100
    )
    assert result["frequencies"] == [20.0, 44.7, 100.0]
    assert result["magnitudes"] == [-42.3, -45.1, -38.7]


def test_spectrum_queries(camilla_mockquery):
    camilla_mockquery.spectrum.get_spectrum(
        side="capture", min_freq=20.0, max_freq=20000.0, n_bins=100
    )
    camilla_mockquery.query.assert_called_with(
        "GetSpectrum",
        value={
            "side": "capture",
            "channel": None,
            "min_freq": 20.0,
            "max_freq": 20000.0,
            "n_bins": 100,
        },
    )

    camilla_mockquery.spectrum.get_spectrum(
        side="playback", min_freq=100.0, max_freq=10000.0, n_bins=50, channel=1
    )
    camilla_mockquery.query.assert_called_with(
        "GetSpectrum",
        value={
            "side": "playback",
            "channel": 1,
            "min_freq": 100.0,
            "max_freq": 10000.0,
            "n_bins": 50,
        },
    )


def test_subscribe_spectrum(camilla_mockquery):
    callback = MagicMock(return_value=False)
    camilla_mockquery.subscribe_events = MagicMock()

    camilla_mockquery.spectrum.subscribe_spectrum(
        callback, side="capture", min_freq=20.0, max_freq=20000.0, n_bins=100
    )
    camilla_mockquery.subscribe_events.assert_called_with(
        command="SubscribeSpectrum",
        event_name="SpectrumEvent",
        callback=callback,
        value={
            "side": "capture",
            "channel": None,
            "min_freq": 20.0,
            "max_freq": 20000.0,
            "n_bins": 100,
        },
    )


def test_subscribe_spectrum_with_rate(camilla_mockquery):
    callback = MagicMock(return_value=False)
    camilla_mockquery.subscribe_events = MagicMock()

    camilla_mockquery.spectrum.subscribe_spectrum(
        callback,
        side="playback",
        min_freq=20.0,
        max_freq=20000.0,
        n_bins=100,
        channel=0,
        max_rate=30.0,
    )
    camilla_mockquery.subscribe_events.assert_called_with(
        command="SubscribeSpectrum",
        event_name="SpectrumEvent",
        callback=callback,
        value={
            "side": "playback",
            "channel": 0,
            "min_freq": 20.0,
            "max_freq": 20000.0,
            "n_bins": 100,
            "max_rate": 30.0,
        },
    )


def test_subscribe_spectrum_events(camilla_mockws):
    camilla_mockws.connect()
    sent = []
    replies = iter(
        [
            reply("SubscribeSpectrum", result="Ok"),
            reply(
                "SpectrumEvent",
                result="Ok",
                value={
                    "frequencies": [20.0, 44.7, 100.0],
                    "magnitudes": [-42.3, -45.1, -38.7],
                },
            ),
            reply("StopSubscription", result="Ok"),
        ]
    )

    camilla_mockws.mockconnection.send = MagicMock(
        side_effect=lambda msg: sent.append(msg)
    )
    camilla_mockws.mockconnection.recv = MagicMock(side_effect=lambda: next(replies))

    events = []

    def on_event(event_data):
        events.append(event_data)
        return False

    camilla_mockws.spectrum.subscribe_spectrum(
        on_event, side="capture", min_freq=20.0, max_freq=20000.0, n_bins=100
    )

    assert events == [
        {
            "frequencies": [20.0, 44.7, 100.0],
            "magnitudes": [-42.3, -45.1, -38.7],
        }
    ]
    assert sent == [
        cmd(
            "SubscribeSpectrum",
            value={
                "side": "capture",
                "channel": None,
                "min_freq": 20.0,
                "max_freq": 20000.0,
                "n_bins": 100,
            },
        ),
        cmd("StopSubscription"),
    ]


def test_subscribe_spectrum_processing_stopped(camilla_mockws):
    """A final event with `ProcessingStopped` ends the subscription."""
    camilla_mockws.connect()
    replies = iter(
        [
            reply("SubscribeSpectrum", result="Ok"),
            reply("SpectrumEvent", result="ProcessingStopped"),
        ]
    )
    camilla_mockws.mockconnection.send = MagicMock()
    camilla_mockws.mockconnection.recv = MagicMock(side_effect=lambda: next(replies))

    with pytest.raises(camilladsp.ProcessingStoppedError):
        camilla_mockws.spectrum.subscribe_spectrum(
            MagicMock(), side="capture", min_freq=20.0, max_freq=20000.0, n_bins=100
        )


def test_spectrum_invalid_side(camilla_mockquery):
    with pytest.raises(ValueError):
        camilla_mockquery.spectrum.get_spectrum(
            side="both", min_freq=20.0, max_freq=20000.0, n_bins=100
        )

    callback = MagicMock()
    with pytest.raises(ValueError):
        camilla_mockquery.spectrum.subscribe_spectrum(
            callback, side="invalid", min_freq=20.0, max_freq=20000.0, n_bins=100
        )
