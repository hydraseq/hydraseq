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

def test_run_convolutions_smoke():
    hdr = Hydraseq('convo')

    hdr.insert("a b c _ALPHA")
    hdr.insert("1 2 3 _DIGIT")

    assert run_convolutions("a b c 1 2 3".split(), hdr) == [[0, 3, ['_ALPHA']], [3, 6, ['_DIGIT']]]
    assert run_convolutions("a b 1 2 3 a b".split(), hdr) == [[2, 5, ['_DIGIT']]]

def test_run_convolutions_overlap():
    hdr = Hydraseq('convo')

    hdr.insert("b a d _1")
    hdr.insert("a n d _2")
    hdr.insert("a d a _3")
    hdr.insert("a n d y _4")
    hdr.insert("a d a n _5")

    tester = "b a d a n d y".split()
    expected = [[0, 3, ['_1']], [1, 4, ['_3']], [1, 5, ['_5']], [3, 6, ['_2']], [3, 7, ['_4']]]
    assert run_convolutions(tester, hdr) == expected

def test_stack():
    sentence = "the quick brown fox jumped over the lazy dog"

    hdq1 = Hydraseq('one')
    for pattern in [
        "the 0_A",
        "quick 0_ADJ",
        "brown 0_ADJ",
        "fox 0_N",
        "fox 0_V",
        "jumped 0_V",
        "over 0_PR",
        "lazy 0_ADJ",
        "dog 0_N"
    ]:
        hdq1.insert(pattern)

    hdq2 = Hydraseq('two')
    for pattern in [
        "0_N _NP_",
        "0_ADJ 0_N _NP_",
        "0_V _VP_",
        "0_ADV 0_V _VP_",
        "0_A 0_N _NP_",
        "0_A 0_ADJ 0_ADJ 0_N _NP_",

    ]:
        hdq2.insert(pattern)
    hdq3 = Hydraseq('three')
    for pattern in [
        "_NP_ _VP_ 3_BINGO"
    ]:
        hdq3.insert(pattern)


    result = [[0, 1, ['0_A']], [1, 2, ['0_ADJ']], [2, 3, ['0_ADJ']], [3, 4, ['0_N', '0_V']], [4, 5, ['0_V']], [5, 6, ['0_PR']], [6, 7, ['0_A']], [7, 8, ['0_ADJ']], [8, 9, ['0_N']]]
    assert run_convolutions(sentence.split(), hdq1, "0_") == result

    encoded = [code[2] for code in run_convolutions(sentence.split(), hdq1, "0_")]
    assert encoded == [['0_A'], ['0_ADJ'], ['0_ADJ'], ['0_N', '0_V'], ['0_V'], ['0_PR'], ['0_A'], ['0_ADJ'], ['0_N']]

    result = [[0, 4, ['_NP_']], [2, 4, ['_NP_']], [3, 4, ['_NP_', '_VP_']], [4, 5, ['_VP_']], [7, 9, ['_NP_']], [8, 9, ['_NP_']]]
    assert run_convolutions(encoded, hdq2, "_") == result

    encoded2 = [code[2] for code in run_convolutions(encoded, hdq2, "_")]
    assert encoded2 == [['_NP_'], ['_NP_'], ['_NP_', '_VP_'], ['_VP_'], ['_NP_'], ['_NP_']]

    result = [[1, 3, ['3_BINGO']], [2, 4, ['3_BINGO']]]
    assert run_convolutions(encoded2, hdq3, "3_") == result

def test_face():
    sentence = "bule bule ndad de hule o o db v u v junk junk other stuff"

    hdq1 = Hydraseq('one')
    for pattern in [
        "o 0_eye",
        "db 0_nose",
        "v 0_left_mouth",
        "u 0_mid_mouth",
        "v 0_right_mouth",
    ]:
        hdq1.insert(pattern)

    hdq2 = Hydraseq('two')
    for pattern in [
        "0_eye 0_eye 1_eyes",
        "0_nose 1_nose",
        "0_left_mouth 0_mid_mouth 0_right_mouth 1_mouth",
    ]:
        hdq2.insert(pattern)
    hdq3 = Hydraseq('three')
    for pattern in [
        "1_eyes 1_nose 1_mouth 2_FACE"
    ]:
        hdq3.insert(pattern)

    result = [
        [5, 6, ['0_eye']],
        [6, 7, ['0_eye']],
        [7, 8, ['0_nose']],
        [8, 9, ['0_left_mouth', '0_right_mouth']],
        [9, 10, ['0_mid_mouth']],
        [10, 11, ['0_left_mouth', '0_right_mouth']]
        ]
    assert run_convolutions(sentence, hdq1, "0_") == result

    encoded = [code[2] for code in run_convolutions(sentence, hdq1, "0_")]
    assert encoded == [
        ['0_eye'],
        ['0_eye'],
        ['0_nose'],
        ['0_left_mouth', '0_right_mouth'],
        ['0_mid_mouth'],
        ['0_left_mouth', '0_right_mouth']
        ]

    result = [[0, 2, ['1_eyes']], [2, 3, ['1_nose']], [3, 6, ['1_mouth']]]
    assert run_convolutions(encoded, hdq2, "1_") == result

    encoded2 = [code[2] for code in run_convolutions(encoded, hdq2, "1_")]
    assert encoded2 == [['1_eyes'], ['1_nose'], ['1_mouth']]

    result = [[0, 3, ['2_FACE']]]
    assert run_convolutions(encoded2, hdq3, "2_") == result