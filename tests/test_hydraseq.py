import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq
from hydra import Hydra
from hydraseq import *
from columns import *
sys.path.append('./tests/data/')
import shapes as shapes
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

def test_01_01_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b']])
    check_active( hdr, 1, ['a b'], ['b'])
    check_next(   hdr, 0, [], [])

    hdr.look_ahead([['a']])
    check_active( hdr, 1, ['a'],   ['a'])
    check_next(hdr, 1, ['a b'], ['b'])

def test_01_02_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b']])
    hdr.insert([['a'], ['c']])
    check_active(hdr, 1, ['a c'], ['c'])
    check_next(  hdr, 0, [],                 [])

    hdr.look_ahead([['a']])
    check_active(hdr, 1, ['a'], ['a'])
    check_next(hdr, 2, ['a b', 'a c'], ['b', 'c'])

    hdr.look_ahead([['a'], ['b', 'c']])
    check_active(hdr, 2, ['a b','a c'], ['b','c'])
    check_next(hdr, 0, [], [])

def test_01_02_01_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b'], ['d']])
    hdr.insert([['a'], ['c'], ['d']])
    check_active(hdr, 1, ['a c d'], ['d'])
    check_next(hdr, 0, [], [])

    hdr.look_ahead([['a'],['b','c']])
    check_active(hdr, 2, ['a b', 'a c'], ['b', 'c'])
    check_next(  hdr, 2, ['a b d', 'a c d'],        ['d'])

    hdr.look_ahead([['a']])
    check_active(hdr, 1, ['a'], ['a'])
    check_next(hdr, 2, ['a b', 'a c'], ['b', 'c'])

    hdr.look_ahead([['a'],['b','c'],['d']])
    check_active(hdr, 2, ['a b d', 'a c d'], ['d'])
    check_next(hdr, 0, [], [])

def test_01_02_01_B_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b'], ['d']])
    hdr.insert([['a'], ['c'], ['d']])
    check_active(hdr, 1, ['a c d'], ['d'])
    check_next(hdr, 0, [], [])

    hdr.look_ahead([['a'],['b']])
    check_active(hdr, 1, ['a b'], ['b'])
    check_next(  hdr, 1, ['a b d'],        ['d'])

    hdr.look_ahead([['a'],['c']])
    check_active(hdr, 1, ['a c'], ['c'])
    check_next(  hdr, 1, ['a c d'],        ['d'])

    hdr.look_ahead([['a'],['b','c'],['d']])
    check_active(hdr, 2, ['a b d', 'a c d'], ['d'])
    check_next(  hdr, 0, [], [])

def test_01_02_01_01_sequence():
    hdr = Hydraseq('main')

    hdr.insert([['a'], ['b'], ['d'], ['e']])
    hdr.insert([['a'], ['c'], ['d'], ['e']])
    check_active(hdr, 1, ['a c d e'], ['e'])
    check_next(hdr, 0, [], [])

    hdr.look_ahead([['a']])
    check_active(hdr, 1, ['a'], ['a'])
    check_next(hdr, 2, ['a b', 'a c'], ['b', 'c'])

    hdr.look_ahead([['a'], ['b', 'f']])
    check_active(hdr, 1, ['a b'], ['b'])
    check_next(hdr, 1, ['a b d'], ['d'])

    hdr.look_ahead([['a'], ['b', 'c'],['d']])
    check_active(hdr, 2, ['a b d', 'a c d'], ['d'])
    check_next(hdr, 2, ['a b d e', 'a c d e'], ['e'])

    hdr.look_ahead([['a'], ['b'],['d']])
    check_active(hdr, 1, ['a b d'], ['d'])
    check_next(hdr, 1, ['a b d e'], ['e'])

    hdr.look_ahead([['a'], ['b']])
    check_active(hdr, 1, ['a b'], ['b'])
    check_next(hdr, 1, ['a b d'], ['d'])

def test_sentence():
    hdr = Hydraseq('main')

    hdr.insert("The quick brown fox jumped over the lazy dog")
    assert hdr.look_ahead("The quick brown").get_next_values() == ['fox']

    hdr.insert("The quick brown cat jumped over the lazy dog")
    assert hdr.look_ahead("The quick brown").get_next_values() == ['cat', 'fox']

    hdr.insert("The quick brown cat jumped over the lazy hound")
    assert hdr.look_ahead("The quick brown").get_next_values() == ['cat', 'fox']

    hdr.look_ahead([['The'],['quick'],['brown'],['fox','cat']])
    check_active(hdr, 2, ['The quick brown cat', 'The quick brown fox'], ['cat', 'fox'])
    check_next(  hdr, 2, ['The quick brown cat jumped','The quick brown fox jumped'],['jumped'] )


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

def test_run_convolutions_smoke():
    hdr = Hydraseq('_')

    hdr.insert("a b c _ALPHA")
    hdr.insert("1 2 3 _DIGIT")

    assert hdr.convolutions("a b c 1 2 3".split()) == [[0, 3, ['_ALPHA']], [3, 6, ['_DIGIT']]]
    assert hdr.convolutions("a b 1 2 3 a b".split()) == [[2, 5, ['_DIGIT']]]

def test_run_convolutions_overlap():
    hdr = Hydraseq('_')

    hdr.insert("b a d _1")
    hdr.insert("a n d _2")
    hdr.insert("a d a _3")
    hdr.insert("a n d y _4")
    hdr.insert("a d a n _5")

    tester = "b a d a n d y".split()
    expected = [[0, 3, ['_1']], [1, 4, ['_3']], [1, 5, ['_5']], [3, 6, ['_2']], [3, 7, ['_4']]]
    assert hdr.convolutions(tester) == expected

def test_get_downwards():
    hds = Hydraseq("_")

    hds.insert("a b c _D")
    hds.insert("e f g _D")
    hds.insert("c e f _D")

    assert get_downwards(hds, ["_D"]) == ['a', 'b', 'c', 'e', 'f', 'g']

def test_reverse_convo():
    hdq1 = Hydraseq('0_')
    for pattern in [
        "o 0_eye",
        "db 0_nose",
        "v 0_left_mouth",
        "u 0_mid_mouth",
        "v 0_right_mouth",
    ]:
        hdq1.insert(pattern)

    hdq2 = Hydraseq('1_')
    for pattern in [
        "0_eye 0_eye 1_eyes",
        "0_nose 1_nose",
        "0_left_mouth 0_mid_mouth 0_right_mouth 1_mouth",
    ]:
        hdq2.insert(pattern)
    hdq3 = Hydraseq('2_')
    for pattern in [
        "1_eyes 1_nose 1_mouth 2_FACE"
    ]:
        hdq3.insert(pattern)

    assert reverse_convo([hdq1, hdq2, hdq3], "2_FACE") == ['db', 'o', 'u', 'v']

def test_get_sequence_nodes():
    hds = Hydraseq('_')
    hds.insert('a b c d e f g h i j')

    nxt = hds.look_ahead('a b c d e f g h i').next_nodes.pop()
    assert nxt.get_sequence() == 'a b c d e f g h i j'
    assert str(nxt.get_sequence_nodes()) == '[[a], [b], [c], [d], [e], [f], [g], [h], [i]]'

def test_get_sequence_nodes_out_of_order():
    hds1 = Hydraseq('_')
    hds1.insert('C A B')

    nxt1 = hds1.look_ahead('C A').next_nodes.pop()
    assert nxt1.get_sequence() == 'C A B'


def test_get_sequence_multiple():
    hds2 = Hydraseq('_')
    hds2.insert([['a'], ['B'],['c']])
    hds2.insert([['a'], ['b'],['c']])

    nxts = hds2.look_ahead([['a'], ['b','B']]).next_nodes
    assert sorted([str(nxt.get_sequence_nodes()) for nxt in nxts]) == ['[[a], [B]]', '[[a], [b]]']

def test_self_insert():
    hdq = Hydraseq('_')
    hdq.self_insert("Burger King wants people to download its app. So it's sending them to McDonald's for access to a one-cent Whopper.")
    assert len(hdq.columns) == 38
    assert sorted(hdq.look_ahead("Burger King wants").get_next_values()) == sorted(['people', '_3'])
    assert sorted(hdq.look_ahead("Burger King wants").get_active_values()) == sorted(['wants'])


def test_hydra():
    words = ['every', 'good', 'boy', 'does', 'fine', 'everything']

    hh = Hydra(words)

    for idx, word in enumerate(words):
        hh.insert_word(word, idx)
    for idx, word in enumerate(words):
        hh.insert_word(word, idx*2)

    assert hh.lookup('every') == set([0])
    assert hh.lookup('good')  == set([1,2])
    assert hh.lookup('boy')   == set([2,4])
    assert hh.lookup('does')  == set([3,6])
    assert hh.lookup('fine')  == set([4,8])

def test_negative_hydra():
    hh = Hydra([])

    hh.insert_word('someword', 'marker')

    assert hh.lookup('anotherword') == None


def test_coordinate_hydra():
    hx = Hydra([])
    hy = Hydra([])

    points = {
        'a': [0.123456, 0.56789],
        'b': [0.1234, 0.5678]
    }

    for point, xy in points.items():
        hx.insert_word(str(xy[0]), point)
        hy.insert_word(str(xy[1]), point)


    assert sorted(hx.get_level(str(0.1234)).keys()) == sorted(['_', '5'])

