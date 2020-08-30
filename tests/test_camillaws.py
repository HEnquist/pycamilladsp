import pytest
from unittest.mock import MagicMock
import camilladsp

class DummyWS:
    def __init__(self):
        self.query = None
        self.response = None

    responses = {
        "getstate": "OK:GETSTATE:IDLE",
        "getversion": "OK:GETVERSION:0.3.2",
        "getsignalrange": "OK:GETSIGNALRANGE:0.2",
        "getcapturerate": "OK:GETCAPTURERATE:88250",

    }

    def send(self, query):
        self.query = query
        if query in self.responses:
            self.response = self.responses[query]
        else:
            self.response = "ERROR:INVALID"

    def recv(self):
        return self.response


@pytest.fixture
def camillaws():
    connection = MagicMock()
    camilladsp.camilladsp.create_connection = MagicMock(return_value=connection)

    ws_dummy = DummyWS()
    connection.send = MagicMock(side_effect=ws_dummy.send)
    connection.recv = MagicMock(side_effect=ws_dummy.recv)

    cdsp = camilladsp.camilladsp.CamillaConnection("localhost", 1234)
    return cdsp



def test_state(camillaws):
    camillaws.connect()
    assert camillaws.get_state() == "IDLE"

def test_signal_range(camillaws):
    camillaws.connect()
    assert camillaws.get_signal_range() == 0.2

def test_signal_range_dB(camillaws):
    camillaws.connect()
    assert camillaws.get_signal_range_dB() == -20

def test_capture_rate(camillaws):
    camillaws.connect()
    assert camillaws.get_capture_rate() == 88200
    assert camillaws.get_capture_rate_raw() == 88250