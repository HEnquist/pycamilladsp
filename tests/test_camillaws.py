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
        '"GetErrorValue"': json.dumps(
            {"GetErrorValue": {"result": "Error", "value": "badstuff"}}
        ),
        '"GetError"': json.dumps({"GetError": {"result": "Error"}}),
        '"Invalid"': json.dumps({"Invalid": {"result": "Error", "value": "badstuff"}}),
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
        '"NotACommand"': json.dumps({"Invalid": {"result": "Error"}}),
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
            self.response = json.dumps(
                {"Invalid": {"result": "Error", "value": "badstuff"}}
            )

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
    camilla_mockquery.rate.capture()
    camilla_mockquery.query.assert_called_with("GetCaptureRate")
    camilla_mockquery.rate.capture_raw()
    camilla_mockquery.query.assert_called_with("GetCaptureRate")
    camilla_mockquery.levels.range()
    camilla_mockquery.query.assert_called_with("GetSignalRange")
    camilla_mockquery.levels.range_decibel()
    camilla_mockquery.query.assert_called_with("GetSignalRange")
    camilla_mockquery.settings.set_update_interval(1234)
    camilla_mockquery.query.assert_called_with("SetUpdateInterval", arg=1234)
    camilla_mockquery.settings.update_interval()
    camilla_mockquery.query.assert_called_with("GetUpdateInterval")
    camilla_mockquery.general.stop()
    camilla_mockquery.query.assert_called_with("Stop")
    camilla_mockquery.general.exit()
    camilla_mockquery.query.assert_called_with("Exit")
    camilla_mockquery.general.reload()
    camilla_mockquery.query.assert_called_with("Reload")
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
    camilla_mockquery.status.rate_adjust()
    camilla_mockquery.query.assert_called_with("GetRateAdjust")
    camilla_mockquery.status.buffer_level()
    camilla_mockquery.query.assert_called_with("GetBufferLevel")
    camilla_mockquery.status.clipped_samples()
    camilla_mockquery.query.assert_called_with("GetClippedSamples")
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
    camilla_mockquery.levels.capture_rms()
    camilla_mockquery.query.assert_called_with("GetCaptureSignalRms")
    camilla_mockquery.levels.capture_peak()
    camilla_mockquery.query.assert_called_with("GetCaptureSignalPeak")
    camilla_mockquery.levels.playback_rms()
    camilla_mockquery.query.assert_called_with("GetPlaybackSignalRms")
    camilla_mockquery.levels.playback_peak()
    camilla_mockquery.query.assert_called_with("GetPlaybackSignalPeak")


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
