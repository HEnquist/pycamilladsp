import pytest
from camilladsp import filter_eval
import numpy as np

def test_24bit():
    filt = filter_eval.Conv(None, 44100)
    vect = np.asarray([1, 0, 0, -1, 0, 0, 0, 0, 1], dtype=np.int8)
    expected = np.array([1/(2**7-1), -1/(2**7-1), 1/(2**23-1)])
    new_vect = filt._repack_24bit(vect)
    assert abs(np.sum(new_vect-expected))<1e-15 


