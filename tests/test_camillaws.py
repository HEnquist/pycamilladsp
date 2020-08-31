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
    }

    def send(self, query):
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
        yield cdsp

@pytest.fixture
def camilla():
    cdsp = camilladsp.camilladsp.CamillaConnection("localhost", 1234)
    yield cdsp


def test_connect(camilla_mockws):
    with pytest.raises(IOError):
        camilla_mockws.get_state()
    camilla_mockws.connect()
    assert camilla_mockws.is_connected()
    assert camilla_mockws.get_state() == "IDLE"
    camilla_mockws.disconnect()
    assert not camilla_mockws.is_connected()


def test_signal_range(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_signal_range() == 0.2

def test_signal_range_dB(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_signal_range_dB() == -20

def test_capture_rate(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws.get_capture_rate() == 88200
    assert camilla_mockws.get_capture_rate_raw() == 88250

def test_query(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws._query("teststring") == "some:long_string\nwith:stuff"

def test_query_setvalue(camilla_mockws):
    camilla_mockws.connect()
    assert camilla_mockws._query("setsomevalue", arg=123) is None
    assert camilla_mockws.dummyws.response == "OK:SETSOMEVALUE"
    assert camilla_mockws.dummyws.value == "123"

def test_parse_response(camilla):
    assert camilla._parse_response("OK:DUMMY:5") == ("OK", 'dummy', '5')