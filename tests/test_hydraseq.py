import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq
from hydraseq import run_convolutions
import pytest

def w(str_sentence):
    return re.findall(r"[\w']+>[.,!?;]", str_sentence)

def check_active(hdr, num_active_nodes, active_sequences, active_values):
    assert len(hdr.active_nodes) == num_active_nodes
    assert hdr.get_active_sequences() == active_sequences
    assert hdr.get_active_values() == active_values

def check_next(hdr, num_next_nodes, next_sequences, next_values):
    assert len(hdr.next_nodes) == num_next_nodes
    assert hdr.get_next_sequences() == next_sequences
    assert hdr.get_next_values() == next_values

@pytest.mark.smoke
def test_01_01_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b']])
    check_active( hdr, 1, ['(*) a b'], ['b'])
    check_next(   hdr, 0, [], [])

    hdr.look_ahead([['a']])
    check_active( hdr, 1, ['(*) a'],   ['a'])
    check_next(hdr, 1, ['(*) a b'], ['b'])

def test_01_02_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b', 'c']])
    check_active(hdr, 2, ['(*) a b', '(*) a c'], ['b', 'c'])
    check_next(  hdr, 0, [],                 [])

    hdr.look_ahead([['a']])
    check_active(hdr, 1, ['(*) a'], ['a'])
    check_next(hdr, 2, ['(*) a b', '(*) a c'], ['b', 'c'])

    hdr.look_ahead([['a'], ['b', 'c']])
    check_active(hdr, 2, ['(*) a b','(*) a c'], ['b','c'])
    check_next(hdr, 0, [], [])

def test_01_02_01_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b', 'c'], ['d']])
    check_active(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])
    check_next(hdr, 0, [], [])

    hdr.look_ahead([['a'],['b','c']])
    check_active(hdr, 2, ['(*) a b', '(*) a c'], ['b', 'c'])
    check_next(  hdr, 1, ['((*) a b|(*) a c) d'],        ['d'])

    hdr.look_ahead([['a']])
    check_active(hdr, 1, ['(*) a'], ['a'])
    check_next(hdr, 2, ['(*) a b', '(*) a c'], ['b', 'c'])

    hdr.look_ahead([['a'],['b','c'],['d']])
    check_active(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])
    check_next(hdr, 0, [], [])

def test_01_02_01_B_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b', 'c'], ['d']])
    check_active(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])
    check_next(hdr, 0, [], [])

    hdr.look_ahead([['a'],['b']])
    check_active(hdr, 1, ['(*) a b'], ['b'])
    check_next(  hdr, 1, ['((*) a b|(*) a c) d'],        ['d'])

    hdr.look_ahead([['a'],['c']])
    check_active(hdr, 1, ['(*) a c'], ['c'])
    check_next(  hdr, 1, ['((*) a b|(*) a c) d'],        ['d'])

    hdr.look_ahead([['a'],['b','c'],['d']])
    check_active(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])
    check_next(  hdr, 0, [], [])

def test_01_02_01_01_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b', 'c'], ['d'], ['e']])
    check_active(hdr, 1, ['((*) a b|(*) a c) d e'], ['e'])
    check_next(hdr, 0, [], [])

    hdr.look_ahead([['a']])
    check_active(hdr, 1, ['(*) a'], ['a'])
    check_next(hdr, 2, ['(*) a b', '(*) a c'], ['b', 'c'])

    hdr.look_ahead([['a'], ['b', 'f']])
    check_active(hdr, 1, ['(*) a b'], ['b'])
    check_next(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])

    hdr.look_ahead([['a'], ['b', 'c'],['d']])
    check_active(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])
    check_next(hdr, 1, ['((*) a b|(*) a c) d e'], ['e'])

    hdr.look_ahead([['a'], ['b'],['d']])
    check_active(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])
    check_next(hdr, 1, ['((*) a b|(*) a c) d e'], ['e'])

    hdr.look_ahead([['a'], ['b']])
    check_active(hdr, 1, ['(*) a b'], ['b'])
    check_next(hdr, 1, ['((*) a b|(*) a c) d'], ['d'])

def test_sentence():
    hdr = Hydraseq('main')

    hdr.insert("The quick brown fox jumped over the lazy dog")
    assert hdr.look_ahead("The quick brown").get_next_values() == ['fox']

    hdr.insert("The quick brown cat jumped over the lazy dog")
    assert hdr.look_ahead("The quick brown").get_next_values() == ['cat', 'fox']

    hdr.insert("The quick brown cat jumped over the lazy hound")
    assert hdr.look_ahead("The quick brown").get_next_values() == ['cat', 'fox']

    hdr.look_ahead([['The'],['quick'],['brown'],['fox','cat']])
    check_active(hdr, 2, ['(*) The quick brown cat', '(*) The quick brown fox'], ['cat', 'fox'])
    check_next(  hdr, 2, ['(*) The quick brown cat jumped','(*) The quick brown fox jumped'],['jumped'] )

def test_multi_paths():
    hdr = Hydraseq('main')

    hdr.insert([['c', 'd'],
                ['a', 'o'],
                ['t', 'g']])

    check_active(hdr, 2, ['(((*) c|(*) d) a|((*) c|(*) d) o) g',
     '(((*) c|(*) d) a|((*) c|(*) d) o) t'], ['g','t'] )
    check_next(  hdr , 0, [],[])

    hdr.look_ahead([['c'], ['o'], ['t']])
    check_active(hdr, 1, ['(((*) c|(*) d) a|((*) c|(*) d) o) t'], ['t'])
    check_next(  hdr , 0, [],[])

    hdr.look_ahead([['c'], ['o']])
    check_active(hdr, 1, ['((*) c|(*) d) o'], ['o'])
    check_next(hdr, 2, [
        '(((*) c|(*) d) a|((*) c|(*) d) o) g',
        '(((*) c|(*) d) a|((*) c|(*) d) o) t'], ['g', 't'])


def test_surpise_flag():
    hdr = Hydraseq('main')

    assert hdr.surprise == False

    hdr.insert("This is a test")

    assert hdr.surprise == True

    hdr.insert("This is a test")

    assert hdr.surprise == False

    hdr.insert("This is NOT a test")

    assert hdr.surprise == True

    hdr.insert("This is a test")

    assert hdr.surprise == False

def test_streaming():
    hdr = Hydraseq('streaming')

    hdr.insert("the quick brown fox")

    assert hdr.look_ahead("the quick").get_next_values() == ["brown"]

    hdr.reset()

    assert hdr.look_ahead("the").get_next_values() == ["quick"]
    assert hdr.hit("quick", None).get_next_values() == ["brown"]

def test_cloning_hydra():
    hdr0 = Hydraseq('zero')

    hdr0.insert("the quick brown fox")

    hdr1 = Hydraseq('one', hdr0)

    assert hdr1.look_ahead("the quick").get_next_values() == ["brown"]

    hdr1.reset()

    assert hdr1.look_ahead("the").get_next_values() == ["quick"]
    assert hdr1.hit("quick", None).get_next_values() == ["brown"]

def test_run_convolutions():
    hdr = Hydraseq('convo')

    hdr.insert("a b c _ALPHA")
    hdr.insert("1 2 3 _DIGIT")

    assert run_convolutions(hdr, "a b c 1 2 3".split()) == [[0, 3, ['_ALPHA']], [3, 6, ['_DIGIT']]]
    assert run_convolutions(hdr, "a b 1 2 3 a b".split()) == [[2, 5, ['_DIGIT']]]

def test_run_convolutions():
    hdr = Hydraseq('convo')

    hdr.insert("b a d _1")
    hdr.insert("a n d _2")
    hdr.insert("a d a _3")
    hdr.insert("a n d y _4")
    hdr.insert("a d a n _5")

    tester = "b a d a n d y".split()
    expected = [[0, 3, ['_1']], [1, 4, ['_3']], [1, 5, ['_5']], [3, 6, ['_2']], [3, 7, ['_4']]]
    assert run_convolutions(hdr, tester) == expected
