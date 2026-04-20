from camilladsp import StopReason
import pytest
from unittest.mock import MagicMock, patch
import camilladsp
import json


class DummyWS:
    def __init__(self):
        self.query = None
        self.response = None
        self.value = None

    responses = {
        '"GetState"': json.dumps({"GetState": {"result": "Ok", "value": "Inactive"}}),
        '"GetVersion"': json.dumps({"GetVersion": {"result": "Ok", "value": "0.3.2"}}),
        '"GetSupportedDeviceTypes"': json.dumps(
            {
                "GetSupportedDeviceTypes": {
                    "result": "Ok",
                    "value": [["a", "b"], ["c", "d"]],
                }
            }
        ),
        '"GetSignalRange"': json.dumps(
            {"GetSignalRange": {"result": "Ok", "value": "0.2"}}
        ),
        '"GetCaptureSignalRms"': json.dumps(
            {"GetCaptureSignalRms": {"result": "Ok", "value": [0.1, 0.2]}}
        ),
        '"GetCaptureRate"': json.dumps(
            {"GetCaptureRate": {"result": "Ok", "value": "88250"}}
        ),
        '"GetFaders"': json.dumps(
            {
                "GetFaders": {
                    "result": "Ok",
                    "value": [
                        {"volume": -1, "mute": False},
                        {"volume": -2, "mute": True},
                        {"volume": -3, "mute": False},
                        {"volume": -4, "mute": True},
                        {"volume": -5, "mute": False},
                    ],
                }
            }
        ),
        '{"GetFaderVolume": 1}': json.dumps(
            {"GetFaderVolume": {"result": "Ok", "value": [1, -1.23]}}
        ),
        '{"AdjustFaderVolume": [1, -2.5]}': json.dumps(
            {"AdjustFaderVolume": {"result": "Ok", "value": [1, -3.73]}}
        ),
        '{"GetFaderMute": 1}': json.dumps(
            {"GetFaderMute": {"result": "Ok", "value": [1, False]}}
        ),
        '{"ToggleFaderMute": 1}': json.dumps(
            {"ToggleFaderMute": {"result": "Ok", "value": [1, True]}}
        ),
        '{"GetPlaybackDeviceCapabilities": ["Alsa", "hw:Loopback,0,0"]}': json.dumps(
            {
                "GetPlaybackDeviceCapabilities": {
                    "result": "Ok",
                    "value": {
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
                }
            }
        ),
        '{"GetCaptureDeviceCapabilities": ["Alsa", "hw:Loopback,1,0"]}': json.dumps(
            {
                "GetCaptureDeviceCapabilities": {
                    "result": "Ok",
                    "value": {
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
                }
            }
        ),
        '"GetErrorValue"': json.dumps(
            {"GetErrorValue": {"result": "Error", "value": "badstuff"}}
        ),
        '"GetError"': json.dumps({"GetError": {"result": "Error"}}),
        '"InvalidValue"': json.dumps(
            {
                "InvalidValue": {
                    "result": {"InvalidValueError": "invalid value"},
                    "value": "badstuff",
                }
            }
        ),
        '"InvalidRequest"': json.dumps(
            {
                "InvalidRequest": {
                    "result": {"InvalidRequestError": "invalid request"},
                    "value": "badstuff",
                }
            }
        ),
        '"TooManyRequests"': json.dumps(
            {
                "TooManyRequests": {
                    "result": {"RateLimitExceededError": "too many requests"}
                }
            }
        ),
        '"DeviceBusy"': json.dumps(
            {
                "DeviceBusy": {
                    "result": {"DeviceBusyError": "device is busy"},
                    "value": {"name": "hw:Loopback,0,0"},
                }
            }
        ),
        '"DeviceNotFound"': json.dumps(
            {
                "DeviceNotFound": {
                    "result": {"DeviceNotFoundError": "device not found"},
                    "value": {"name": "missing"},
                }
            }
        ),
        '"DeviceError"': json.dumps(
            {
                "DeviceError": {
                    "result": {"DeviceError": "backend failed"},
                    "value": {"name": "hw:Broken"},
                }
            }
        ),
        '"GetStopReason"': json.dumps(
            {"GetStopReason": {"result": "Ok", "value": "Done"}}
        ),
        '"GetStopReason2"': json.dumps(
            {"GetStopReason": {"result": "Ok", "value": {"CaptureFormatChange": 44098}}}
        ),
        '"GetStopReason3"': json.dumps(
            {
                "GetStopReason": {
                    "result": "Ok",
                    "value": {"CaptureError": "error error"},
                }
            }
        ),
        '"NotACommand"': json.dumps({"Invalid": {"error": "Some error"}}),
        '{"SetSomeValue": 123}': json.dumps({"SetSomeValue": {"result": "Ok"}}),
        '"nonsense"': "abcdefgh",
        '"bug_in_ws"': "OK:OTHER",
    }

    def send(self, query):
        if query == '"fail"':
            raise IOError("not connected")
        self.query = query
        # if ":" in query:
        #    query, val = query.split(":",1)
        #    self.response = "OK:{}".format(query.upper())
        #    self.value = val
        print(query)
        if query in self.responses:
            self.response = self.responses[query]
        else:
            self.response = json.dumps({"Invalid": {"error": "Error"}})

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

    def test_subscribe_vu_events(camilla_mockws):
        camilla_mockws.connect()
        sent = []
        replies = iter(
            [
                json.dumps({"SubscribeVuLevels": {"result": "Ok"}}),
                json.dumps(
                    {
                        "VuLevelsEvent": {
                            "result": "Ok",
                            "value": {
                                "playback_rms": [-20.0, -21.0],
                                "playback_peak": [-10.0, -11.0],
                                "capture_rms": [-30.0, -31.0],
                                "capture_peak": [-12.0, -13.0],
                            },
                        }
                    }
                ),
                json.dumps({"StopSubscription": {"result": "Ok"}}),
            ]
        )

        camilla_mockws.mockconnection.send = MagicMock(
            side_effect=lambda msg: sent.append(msg)
        )
        camilla_mockws.mockconnection.recv = MagicMock(
            side_effect=lambda: next(replies)
        )

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
            json.dumps(
                {
                    "SubscribeVuLevels": {
                        "max_rate": 30.0,
                        "attack": 10.0,
                        "release": 200.0,
                    }
                }
            ),
            json.dumps("StopSubscription"),
        ]

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
    camilla_mockws.dummyws.responses['"GetSignalRange"'] = json.dumps(
        {"GetSignalRange": {"result": "Ok", "value": "0.0"}}
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
    camilla_mockws.dummyws.responses['"GetStopReason"'] = (
        camilla_mockws.dummyws.responses['"GetStopReason2"']
    )
    assert camilla_mockws.general.stop_reason() == StopReason.CAPTUREFORMATCHANGE
    assert camilla_mockws.general.stop_reason().data == 44098
    camilla_mockws.dummyws.responses['"GetStopReason"'] = (
        camilla_mockws.dummyws.responses['"GetStopReason3"']
    )
    assert camilla_mockws.general.stop_reason() == StopReason.CAPTUREERROR
    assert camilla_mockws.general.stop_reason().data == "error error"


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
        camilla_mockws.query("NotACommand")
    with pytest.raises(IOError):
        camilla_mockws.query("fail")


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
    assert busy_exc.value.value == {"name": "hw:Loopback,0,0"}

    with pytest.raises(camilladsp.DeviceNotFoundError) as missing_exc:
        camilla_mockws.query("DeviceNotFound")
    assert missing_exc.value.message == "device not found"
    assert missing_exc.value.value == {"name": "missing"}

    with pytest.raises(camilladsp.DeviceError) as device_exc:
        camilla_mockws.query("DeviceError")
    assert device_exc.value.message == "backend failed"
    assert device_exc.value.value == {"name": "hw:Broken"}


def test_query_mockedws(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.query("SetSomeValue", arg=123) is None
    assert camilla_mockws.dummyws.query == json.dumps({"SetSomeValue": 123})
    assert camilla_mockws.general.supported_device_types() == (["a", "b"], ["c", "d"])
    assert camilla_mockws.volume.volume(1) == -1.23
    assert camilla_mockws.volume.adjust_volume(1, -2.5) == -3.73
    assert camilla_mockws.volume.mute(1) == False
    assert camilla_mockws.volume.toggle_mute(1) == True
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

    # settings
    camilla_mockquery.settings.set_update_interval(1234)
    camilla_mockquery.query.assert_called_with("SetUpdateInterval", arg=1234)
    camilla_mockquery.settings.update_interval()
    camilla_mockquery.query.assert_called_with("GetUpdateInterval")

    # general
    camilla_mockquery.general.stop()
    camilla_mockquery.query.assert_called_with("Stop")
    camilla_mockquery.general.exit()
    camilla_mockquery.query.assert_called_with("Exit")
    camilla_mockquery.general.reload()
    camilla_mockquery.query.assert_called_with("Reload")
    camilla_mockquery.general.playback_device_capabilities("Alsa", "hw:Loopback,0,0")
    camilla_mockquery.query.assert_called_with(
        "GetPlaybackDeviceCapabilities", arg=("Alsa", "hw:Loopback,0,0")
    )
    camilla_mockquery.general.capture_device_capabilities("Alsa", "hw:Loopback,1,0")
    camilla_mockquery.query.assert_called_with(
        "GetCaptureDeviceCapabilities", arg=("Alsa", "hw:Loopback,1,0")
    )

    # config
    camilla_mockquery.config.file_path()
    camilla_mockquery.query.assert_called_with("GetConfigFilePath")
    camilla_mockquery.config.set_file_path("some/path")
    camilla_mockquery.query.assert_called_with("SetConfigFilePath", arg="some/path")
    camilla_mockquery.config.active_raw()
    camilla_mockquery.query.assert_called_with("GetConfig")
    camilla_mockquery.config.active_json()
    camilla_mockquery.query.assert_called_with("GetConfigJson")
    camilla_mockquery.config.set_active_raw("some:yaml")
    camilla_mockquery.query.assert_called_with("SetConfig", arg="some:yaml")
    camilla_mockquery.config.set_active_json("{'some': 'json'}")
    camilla_mockquery.query.assert_called_with("SetConfigJson", arg="{'some': 'json'}")
    camilla_mockquery.config.set_active({"some": "yaml"})
    camilla_mockquery.query.assert_called_with("SetConfig", arg="some: yaml\n")
    camilla_mockquery.config.get_value("some")
    camilla_mockquery.query.assert_called_with("GetConfigValue", arg="some")
    camilla_mockquery.config.set_value("some", "value")
    camilla_mockquery.query.assert_called_with("SetConfigValue", arg=("some", "value"))
    camilla_mockquery.config.patch({"some": "value"})
    camilla_mockquery.query.assert_called_with("PatchConfig", arg={"some": "value"})

    # status
    camilla_mockquery.status.rate_adjust()
    camilla_mockquery.query.assert_called_with("GetRateAdjust")
    camilla_mockquery.status.buffer_level()
    camilla_mockquery.query.assert_called_with("GetBufferLevel")
    camilla_mockquery.status.clipped_samples()
    camilla_mockquery.query.assert_called_with("GetClippedSamples")
    camilla_mockquery.status.processing_load()
    camilla_mockquery.query.assert_called_with("GetProcessingLoad")
    camilla_mockquery.status.resampler_load()
    camilla_mockquery.query.assert_called_with("GetResamplerLoad")

    # volume & mute
    camilla_mockquery.volume.main_volume()
    camilla_mockquery.query.assert_called_with("GetVolume")
    camilla_mockquery.volume.set_main_volume(-25.0)
    camilla_mockquery.query.assert_called_with("SetVolume", arg=-25.0)
    camilla_mockquery.volume.set_volume(1, -1.23)
    camilla_mockquery.query.assert_called_with("SetFaderVolume", arg=(1, -1.23))
    camilla_mockquery.volume.main_mute()
    camilla_mockquery.query.assert_called_with("GetMute")
    camilla_mockquery.volume.set_main_mute(False)
    camilla_mockquery.query.assert_called_with("SetMute", arg=False)
    camilla_mockquery.volume.set_mute(1, False)
    camilla_mockquery.query.assert_called_with("SetFaderMute", arg=(1, False))


def test_queries_adv(camilla_mockquery_yaml):
    camilla_mockquery_yaml.config.read_and_parse_file("some/path")
    camilla_mockquery_yaml.query.assert_called_with("ReadConfigFile", arg="some/path")
    camilla_mockquery_yaml.config.parse_yaml("rawyaml")
    camilla_mockquery_yaml.query.assert_called_with("ReadConfig", arg="rawyaml")
    camilla_mockquery_yaml.config.validate({"some": "yaml"})
    camilla_mockquery_yaml.query.assert_called_with(
        "ValidateConfig", arg="some: yaml\n"
    )
    camilla_mockquery_yaml.config.active()
    camilla_mockquery_yaml.query.assert_called_with("GetConfig")
    camilla_mockquery_yaml.config.previous()
    camilla_mockquery_yaml.query.assert_called_with("GetPreviousConfig")


def test_queries_customreplies(camilla_mockquery):
    camilla_mockquery.query.return_value = [0, -12.0]
    camilla_mockquery.volume.adjust_volume(0, -5.0)
    camilla_mockquery.query.assert_called_with("AdjustFaderVolume", arg=(0, -5.0))
    camilla_mockquery.volume.adjust_volume(0, -5.0, min_limit=-20, max_limit=3.0)
    camilla_mockquery.query.assert_called_with(
        "AdjustFaderVolume", arg=(0, (-5.0, -20.0, 3.0))
    )
    camilla_mockquery.volume.adjust_volume(0, -5.0, min_limit=-20)
    camilla_mockquery.query.assert_called_with(
        "AdjustFaderVolume", arg=(0, (-5.0, -20.0, 50.0))
    )
    camilla_mockquery.volume.adjust_volume(0, -5.0, max_limit=3.0)
    camilla_mockquery.query.assert_called_with(
        "AdjustFaderVolume", arg=(0, (-5.0, -150.0, 3.0))
    )


def test_subscribe_signal_levels(camilla_mockquery):
    callback = MagicMock(return_value=False)
    camilla_mockquery.subscribe_events = MagicMock()

    camilla_mockquery.levels.subscribe_signal_levels(callback, side="playback")

    camilla_mockquery.subscribe_events.assert_called_with(
        command="SubscribeSignalLevels",
        arg="playback",
        event_name="SignalLevelsEvent",
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
        arg={"max_rate": 30.0, "attack": 10.0, "release": 200.0},
        event_name="VuLevelsEvent",
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
        arg={"max_rate": 30.0, "attack": 10.0, "release": 200.0},
        event_name="VuLevelsEvent",
        callback=callback,
    )


def test_subscribe_events(camilla_mockws):
    camilla_mockws.connect()
    sent = []
    replies = iter(
        [
            json.dumps({"SubscribeSignalLevels": {"result": "Ok"}}),
            json.dumps(
                {
                    "SignalLevelsEvent": {
                        "result": "Ok",
                        "value": {
                            "side": "capture",
                            "rms": [-58.1, -57.6],
                            "peak": [-39.4, -38.9],
                        },
                    }
                }
            ),
            json.dumps({"StopSubscription": {"result": "Ok"}}),
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
        arg="capture",
        event_name="SignalLevelsEvent",
        callback=on_event,
    )

    assert sent == [
        json.dumps({"SubscribeSignalLevels": "capture"}),
        '"StopSubscription"',
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
            json.dumps({"SubscribeVuLevels": {"result": "Ok"}}),
            json.dumps(
                {
                    "VuLevelsEvent": {
                        "result": "Ok",
                        "value": {
                            "playback_rms": [-20.0, -21.0],
                            "playback_peak": [-10.0, -11.0],
                            "capture_rms": [-30.0, -31.0],
                            "capture_peak": [-12.0, -13.0],
                        },
                    }
                }
            ),
            json.dumps({"StopSubscription": {"result": "Ok"}}),
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
        json.dumps(
            {"SubscribeVuLevels": {"max_rate": 30.0, "attack": 10.0, "release": 200.0}}
        ),
        json.dumps("StopSubscription"),
    ]
