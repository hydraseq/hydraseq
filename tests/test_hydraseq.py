import re
import sys
sys.path.append('.')
from hydraseq.hydraseq import Hydraseq
import pytest

def w(str_sentence):
    return re.findall(r"[\w']+|[.,!?;]", str_sentence)
#@pytest.mark.skip
def test_smoke():
    hdr = Hydraseq('main')

    hdr.predict([['a'], ['b']], is_learning=True)
    assert hdr.predict([['a']]).sdr_predicted == ['b']

def test_smoke2():
    hdr = Hydraseq('main')

    hdr.predict([['a'], ['b', 'c']], is_learning=True)
    assert hdr.predict([['a']]).sdr_predicted == ['b', 'c']

def test_smoke3():
    hdr = Hydraseq('main')

    hdr.predict([['a'], ['b', 'c'], ['d']], is_learning=True)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 0

    hdr.predict([['a']], is_learning=True)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 2

    hdr.predict([['a'], ['b', 'c']], is_learning=True)
    assert len(hdr.active) == 2
    assert len(hdr.predicted) == 1

def test_smoke4():
    hdr = Hydraseq('main')

    hdr.predict([['a'], ['b', 'c'], ['d'], ['e']], is_learning=True)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 0

    hdr.predict([['a']], is_learning=False)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 2

    hdr.predict([['a'], ['b', 'f']], is_learning=False)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 1


    hdr.predict([['a'], ['b', 'c'],['d']])
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 1
    assert hdr.sdr_predicted == ['e']


    hdr.predict([['a'], ['b']])
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 1
    assert hdr.sdr_predicted == ['d']


# TODO: this is just a copy of smoke4, left off to write a new test.
def test_smoke5():
    hdr = Hydraseq('main')

    hdr.predict("The quick brown fox jumped over the lazy dog", is_learning=True)
    assert hdr.predict("The quick brown").sdr_predicted == ['fox']

    hdr.predict("The quick brown cat jumped over the lazy dog", is_learning=True)
    assert hdr.predict("The quick brown").sdr_predicted == ['cat', 'fox']



