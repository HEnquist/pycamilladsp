import pytest
from unittest.mock import MagicMock, patch
import camilladsp

class DummyWS:
    def __init__(self):
        self.query = None
        self.response = None
        self.value = None

    responses = {
        "getstate": "OK:GETSTATE:IDLE",
        "getversion": "OK:GETVERSION:0.3.2",
        "getsignalrange": "OK:GETSIGNALRANGE:0.2",
        "getcapturerate": "OK:GETCAPTURERATE:88250",
        "teststring": "OK:TESTSTRING:some:long_string\nwith:stuff",
        "error": "ERROR:ERROR:badstuff",
        "invalid": "ERROR:INVALID",
        "nonsense": "abcdefgh",
        "bug_in_ws": "OK:OTHER",
    }

    def send(self, query):
        if query == "fail":
            raise IOError("not connected")
        self.query = query
        if ":" in query:
            query, val = query.split(":",1)
            self.response = "OK:{}".format(query.upper())
            self.value = val
        elif query in self.responses:
            self.response = self.responses[query]
        else:
            self.response = "ERROR:INVALID"

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
    assert camilla_mockws.get_state() == "IDLE"
    assert camilla_mockws.get_version() == ('0', '3', '2')
    camilla_mockws.disconnect()
    assert not camilla_mockws.is_connected()

def test_connect_fail(camilla):
    with pytest.raises(IOError):
        camilla.connect()

def test_signal_range(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_signal_range() == 0.2

def test_signal_range_dB(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_signal_range_dB() == -20
    camilla_mockws.dummyws.responses["getsignalrange"] = "OK:GETSIGNALRANGE:0.0"
    assert camilla_mockws.get_signal_range_dB() == -1000

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

def test_query(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws._query("teststring") == "some:long_string\nwith:stuff"
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws._query("error")
    with pytest.raises(camilladsp.CamillaError):
        camilla_mockws._query("invalid")
    with pytest.raises(IOError):
        camilla_mockws._query("bug_in_ws") 
    with pytest.raises(IOError):
        camilla_mockws._query("nonsense")
    with pytest.raises(IOError):
        camilla_mockws._query("fail")

def test_query_setvalue(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws._query("setsomevalue", arg=123) is None
    assert camilla_mockws.dummyws.response == "OK:SETSOMEVALUE"
    assert camilla_mockws.dummyws.value == "123"

def test_parse_response(camilla):
    assert camilla._parse_response("OK:DUMMY:5") == ("OK", 'dummy', '5')

def test_queries(camilla_mockquery):
    camilla_mockquery.get_capture_rate()
    camilla_mockquery._query.assert_called_with('getcapturerate')
    camilla_mockquery.get_capture_rate_raw()
    camilla_mockquery._query.assert_called_with('getcapturerate')
    camilla_mockquery.get_signal_range()
    camilla_mockquery._query.assert_called_with('getsignalrange')
    camilla_mockquery.get_signal_range_dB()
    camilla_mockquery._query.assert_called_with('getsignalrange')
    camilla_mockquery.set_update_interval(1234)
    camilla_mockquery._query.assert_called_with('setupdateinterval', arg=1234)
    camilla_mockquery.get_update_interval()
    camilla_mockquery._query.assert_called_with('getupdateinterval')
    camilla_mockquery.stop()
    camilla_mockquery._query.assert_called_with('stop')
    camilla_mockquery.exit()
    camilla_mockquery._query.assert_called_with('exit')
    camilla_mockquery.reload()
    camilla_mockquery._query.assert_called_with('reload')
    camilla_mockquery.get_config_name()
    camilla_mockquery._query.assert_called_with('getconfigname')
    camilla_mockquery.set_config_name("some/path")
    camilla_mockquery._query.assert_called_with('setconfigname', arg="some/path")
    camilla_mockquery.get_config_raw()
    camilla_mockquery._query.assert_called_with('getconfig')
    camilla_mockquery.set_config_raw("some:yaml")
    camilla_mockquery._query.assert_called_with('setconfig', arg="some:yaml")
    camilla_mockquery.set_config({"some":"yaml"})
    camilla_mockquery._query.assert_called_with('setconfig', arg='some: yaml\n')
    camilla_mockquery.get_rate_adjust()
    camilla_mockquery._query.assert_called_with('getrateadjust')

def test_queries_adv(camilla_mockquery_yaml):
    camilla_mockquery_yaml.read_config_file("some/path")
    camilla_mockquery_yaml._query.assert_called_with('readconfigfile', arg="some/path")
    camilla_mockquery_yaml.read_config("rawyaml")
    camilla_mockquery_yaml._query.assert_called_with('readconfig', arg="rawyaml")
    camilla_mockquery_yaml.validate_config({"some":"yaml"})
    camilla_mockquery_yaml._query.assert_called_with('validateconfig', arg='some: yaml\n')
    camilla_mockquery_yaml.get_config()
    camilla_mockquery_yaml._query.assert_called_with('getconfig')
