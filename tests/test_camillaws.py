from camilladsp.camilladsp import StopReason
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
        '"GetSupportedDeviceTypes"': json.dumps({"GetSupportedDeviceTypes": {"result": "Ok", "value": [["a", "b"], ["c", "d"]]}}),
        '"GetSignalRange"': json.dumps({"GetSignalRange": {"result": "Ok", "value": "0.2"}}),
        '"GetCaptureSignalRms"': json.dumps({"GetCaptureSignalRms": {"result": "Ok", "value": [0.1, 0.2]}}),
        '"GetCaptureRate"': json.dumps({"GetCaptureRate": {"result": "Ok", "value": "88250"}}),
        '"GetErrorValue"': json.dumps({"GetErrorValue": {"result": "Error", "value": "badstuff"}}),
        '"GetError"': json.dumps({"GetError": {"result": "Error"}}),
        '"Invalid"': json.dumps({"Invalid": {"result": "Error", "value": "badstuff"}}),
        '"GetStopReason"': json.dumps({"GetStopReason": {"result": "Ok", "value": "Done"}}),
        '"GetStopReason2"': json.dumps({"GetStopReason": {"result": "Ok", "value": {'CaptureFormatChange': 44098}}}),
        '"GetStopReason3"': json.dumps({"GetStopReason": {"result": "Ok", "value": {'CaptureError': 'error error'}}}),
        '"NotACommand"': json.dumps({"Invalid": {"result": "Error"}}),
        '{"SetSomeValue": 123}': json.dumps({"SetSomeValue": {"result": "Ok"}}),
        '"nonsense"': "abcdefgh",
        '"bug_in_ws"': "OK:OTHER",
    }

    def send(self, query):
        if query == '"fail"':
            raise IOError("not connected")
        self.query = query
        #if ":" in query:
        #    query, val = query.split(":",1)
        #    self.response = "OK:{}".format(query.upper())
        #    self.value = val
        print(query)
        if query in self.responses:
            self.response = self.responses[query]
        else:
            self.response = json.dumps({"Invalid": {"result": "Error", "value": "badstuff"}})
        

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
    with patch('camilladsp.camilladsp.create_connection', create_connection):
        cdsp = camilladsp.camilladsp.CamillaConnection("localhost", 1234)
        cdsp.dummyws = ws_dummy
        cdsp.mockconnection = connection
        yield cdsp

@pytest.fixture
def camilla():
    cdsp = camilladsp.camilladsp.CamillaConnection("localhost", 12345)
    yield cdsp

@pytest.fixture
def camilla_mockquery():
    query_dummy = MagicMock()
    with patch('camilladsp.camilladsp.CamillaConnection._query', query_dummy):
        cdsp = camilladsp.camilladsp.CamillaConnection("localhost", 1234)
        yield cdsp

@pytest.fixture
def camilla_mockquery_yaml():
    query_dummy = MagicMock(return_value="some: value\n")
    with patch('camilladsp.camilladsp.CamillaConnection._query', query_dummy):
        cdsp = camilladsp.camilladsp.CamillaConnection("localhost", 1234)
        yield cdsp

def test_connect(camilla_mockws):
    with pytest.raises(IOError):
        camilla_mockws.get_state()
    camilla_mockws.connect()
    assert camilla_mockws.is_connected()
    assert camilla_mockws.get_state() == camilladsp.ProcessingState.INACTIVE
    assert camilla_mockws.get_version() == ('0', '3', '2')
    assert camilla_mockws.get_library_version() == camilladsp.camilladsp._VERSION
    camilla_mockws.disconnect()
    assert not camilla_mockws.is_connected()

def test_connect_fail(camilla):
    with pytest.raises(IOError):
        camilla.connect()

def test_device_types(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_supported_device_types() == (["a", "b"], ["c", "d"])

def test_signal_range(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_signal_range() == 0.2

def test_signal_rms(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_capture_signal_rms() == [0.1, 0.2]

def test_signal_range_db(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_signal_range_db() == -20
    camilla_mockws.dummyws.responses['"GetSignalRange"'] = json.dumps({"GetSignalRange": {"result": "Ok", "value": "0.0"}})
    assert camilla_mockws.get_signal_range_db() == -1000

def test_disconnect_fail(camilla_mockws):
    camilla_mockws.connect()
    def raise_error():
        raise IOError("disconnected")
    camilla_mockws.mockconnection.close = MagicMock(side_effect=raise_error)
    camilla_mockws.disconnect()
    assert not camilla_mockws.is_connected()

def test_capture_rate(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_capture_rate() == 88200
    assert camilla_mockws.get_capture_rate_raw() == 88250

def test_stop_reason(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_stop_reason() == StopReason.DONE
    assert camilla_mockws.get_stop_reason().data == None
    print(camilla_mockws.dummyws.responses)
    camilla_mockws.dummyws.responses['"GetStopReason"'] = camilla_mockws.dummyws.responses['"GetStopReason2"']
    assert camilla_mockws.get_stop_reason() == StopReason.CAPTUREFORMATCHANGE
    assert camilla_mockws.get_stop_reason().data == 44098
    camilla_mockws.dummyws.responses['"GetStopReason"'] = camilla_mockws.dummyws.responses['"GetStopReason3"']
    assert camilla_mockws.get_stop_reason() == StopReason.CAPTUREERROR
    assert camilla_mockws.get_stop_reason().data == "error error"

def test_query(camilla_mockws):
    camilla_mockws.connect()
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws._query("GetError")
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws._query("GetErrorValue")
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws._query("Invalid")
    with pytest.raises(IOError):
        camilla_mockws._query("bug_in_ws") 
    with pytest.raises(IOError):
        camilla_mockws._query("NotACommand")
    with pytest.raises(IOError):
        camilla_mockws._query("fail")

def test_query_mockedws(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws._query("SetSomeValue", arg=123) is None
    assert camilla_mockws.dummyws.query == json.dumps({"SetSomeValue": 123})
    assert camilla_mockws.get_supported_device_types() == (["a", "b"], ["c", "d"])

def test_queries(camilla_mockquery):
    camilla_mockquery.get_capture_rate()
    camilla_mockquery._query.assert_called_with('GetCaptureRate')
    camilla_mockquery.get_capture_rate_raw()
    camilla_mockquery._query.assert_called_with('GetCaptureRate')
    camilla_mockquery.get_signal_range()
    camilla_mockquery._query.assert_called_with('GetSignalRange')
    camilla_mockquery.get_signal_range_db()
    camilla_mockquery._query.assert_called_with('GetSignalRange')
    camilla_mockquery.set_update_interval(1234)
    camilla_mockquery._query.assert_called_with('SetUpdateInterval', arg=1234)
    camilla_mockquery.get_update_interval()
    camilla_mockquery._query.assert_called_with('GetUpdateInterval')
    camilla_mockquery.stop()
    camilla_mockquery._query.assert_called_with('Stop')
    camilla_mockquery.exit()
    camilla_mockquery._query.assert_called_with('Exit')
    camilla_mockquery.reload()
    camilla_mockquery._query.assert_called_with('Reload')
    camilla_mockquery.get_config_name()
    camilla_mockquery._query.assert_called_with('GetConfigName')
    camilla_mockquery.set_config_name("some/path")
    camilla_mockquery._query.assert_called_with('SetConfigName', arg="some/path")
    camilla_mockquery.get_config_raw()
    camilla_mockquery._query.assert_called_with('GetConfig')
    camilla_mockquery.set_config_raw("some:yaml")
    camilla_mockquery._query.assert_called_with('SetConfig', arg="some:yaml")
    camilla_mockquery.set_config({"some":"yaml"})
    camilla_mockquery._query.assert_called_with('SetConfig', arg='some: yaml\n')
    camilla_mockquery.get_rate_adjust()
    camilla_mockquery._query.assert_called_with('GetRateAdjust')
    camilla_mockquery.get_buffer_level()
    camilla_mockquery._query.assert_called_with('GetBufferLevel')
    camilla_mockquery.get_clipped_samples()
    camilla_mockquery._query.assert_called_with('GetClippedSamples')
    camilla_mockquery.get_volume()
    camilla_mockquery._query.assert_called_with('GetVolume')
    camilla_mockquery.set_volume(-25.0)
    camilla_mockquery._query.assert_called_with('SetVolume', arg=-25.0)
    camilla_mockquery.get_mute()
    camilla_mockquery._query.assert_called_with('GetMute')
    camilla_mockquery.set_mute(False)
    camilla_mockquery._query.assert_called_with('SetMute', arg=False)
    camilla_mockquery.get_capture_signal_rms()
    camilla_mockquery._query.assert_called_with('GetCaptureSignalRms')
    camilla_mockquery.get_capture_signal_peak()
    camilla_mockquery._query.assert_called_with('GetCaptureSignalPeak')
    camilla_mockquery.get_playback_signal_rms()
    camilla_mockquery._query.assert_called_with('GetPlaybackSignalRms')
    camilla_mockquery.get_playback_signal_peak()
    camilla_mockquery._query.assert_called_with('GetPlaybackSignalPeak')


def test_queries_adv(camilla_mockquery_yaml):
    camilla_mockquery_yaml.read_config_file("some/path")
    camilla_mockquery_yaml._query.assert_called_with('ReadConfigFile', arg="some/path")
    camilla_mockquery_yaml.read_config("rawyaml")
    camilla_mockquery_yaml._query.assert_called_with('ReadConfig', arg="rawyaml")
    camilla_mockquery_yaml.validate_config({"some":"yaml"})
    camilla_mockquery_yaml._query.assert_called_with('ValidateConfig', arg='some: yaml\n')
    camilla_mockquery_yaml.get_config()
    camilla_mockquery_yaml._query.assert_called_with('GetConfig')
    camilla_mockquery_yaml.get_previous_config()
    camilla_mockquery_yaml._query.assert_called_with('GetPreviousConfig')
