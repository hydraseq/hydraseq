import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq
from hydraseq import *
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

def test_stack():
    sentence = "the quick brown fox jumped over the lazy dog"

    hdq1 = Hydraseq('0_')
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

    hdq2 = Hydraseq('_')
    for pattern in [
        "0_N _NP_",
        "0_ADJ 0_N _NP_",
        "0_V _VP_",
        "0_ADV 0_V _VP_",
        "0_A 0_N _NP_",
        "0_A 0_ADJ 0_ADJ 0_N _NP_",

    ]:
        hdq2.insert(pattern)

    hdq3 = Hydraseq('3_')
    for pattern in [
        "_NP_ _VP_ 3_BINGO"
    ]:
        hdq3.insert(pattern)

    hdq0 = Hydraseq('_')
    hdq0.insert(sentence + " _exit")
    thoughts = think([hdq0, hdq1, hdq2, hdq3])

    assert thoughts == [
        [
            [
                [0, 1, ['the']],
                [1, 2, ['quick']],
                [2, 3, ['brown']],
                [3, 4, ['fox']],
                [4, 5, ['jumped']],
                [5, 6, ['over']],
                [6, 7, ['the']],
                [7, 8, ['lazy']],
                [8, 9, ['dog']]
            ]
        ],
        [
            [
                [0, 1, ['0_A']],
                [1, 2, ['0_ADJ']],
                [2, 3, ['0_ADJ']],
                [3, 4, ['0_N', '0_V']],
                [4, 5, ['0_V']],
                [5, 6, ['0_PR']],
                [6, 7, ['0_A']],
                [7, 8, ['0_ADJ']],
                [8, 9, ['0_N']]
            ]
        ],
        [
            [
                [0, 4, ['_NP_']],
                [4, 5, ['_VP_']]
            ],
            [
                [2, 4, ['_NP_']],
                [4, 5, ['_VP_']]
            ],
            [
                [3, 4, ['_NP_', '_VP_']],
                [4, 5, ['_VP_']]
            ],
            [
                [7, 9, ['_NP_']]
            ],
            [
                [8, 9, ['_NP_']]
            ]
        ],
        [
            [
                [0, 2, ['3_BINGO']]
            ],
            [
                [0, 2, ['3_BINGO']]
            ],
            [
                [0, 2, ['3_BINGO']]
            ]
        ]
    ]


def test_face():
    sentence = "bule bule ndad de hule o o db v u v junk junk other stuff"

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

    # First Round
    results = hdq1.convolutions(sentence)
    assert results == [
        [5, 6, ['0_eye']],
        [6, 7, ['0_eye']],
        [7, 8, ['0_nose']],
        [8, 9, ['0_left_mouth', '0_right_mouth']],
        [9, 10, ['0_mid_mouth']],
        [10, 11, ['0_left_mouth', '0_right_mouth']]
        ]

    encoded = [code[2] for code in results]
    assert encoded == [
        ['0_eye'],
        ['0_eye'],
        ['0_nose'],
        ['0_left_mouth', '0_right_mouth'],
        ['0_mid_mouth'],
        ['0_left_mouth', '0_right_mouth']
        ]
    # Secount Round
    results = hdq2.convolutions(encoded)
    assert results == [[0, 2, ['1_eyes']], [2, 3, ['1_nose']], [3, 6, ['1_mouth']]]

    encoded2 = [code[2] for code in results]
    assert encoded2 == [['1_eyes'], ['1_nose'], ['1_mouth']]
    # Third Round
    results = hdq3.convolutions(encoded2)
    assert results == [[0, 3, ['2_FACE']]]


def test_face_compact():
    sentence = "bule bule ndad de hule o o db v u v junk junk other stuff"

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

    hdq0 = Hydraseq('_')
    hdq0.insert(sentence + " _exit")
    thoughts = think([hdq0, hdq1, hdq2, hdq3])

    assert thoughts[3][0] == [[0, 3, ['2_FACE']]]


def test_double_meaning():
    sentence = "spring leaves spring"

    hdq1 = Hydraseq('0_')
    hdq2 = Hydraseq('1_')
    hdq3 = Hydraseq('2_')

    for pattern in [
        "spring 0_A_",
        "spring 0_V_",
        "leaves 0_N_",
        "leaves 0_V_",
        "fall 0_A_",
        "fall 0_V_"
    ]:
        hdq1.insert(pattern)

    for pattern in [
        "0_N_ 1_NP_",
        "0_A_ 0_N_ 1_NP_",
        "0_V_ 1_VP_",
        "0_V_ 0_N_ 1_VP_"
    ]:
        hdq2.insert(pattern)

    for pattern in [
        "1_NP_ 1_VP_ 2_S_"
    ]:
        hdq3.insert(pattern)

    hdq0 = Hydraseq('_')
    hdq0.insert(sentence + " _exit")
    thoughts = think([hdq0, hdq1, hdq2, hdq3])
    assert thoughts[3] == [[[0, 2, ['2_S_']]], [[1, 3, ['2_S_']]]]

def test_think():
    hd1 = Hydraseq('1_')
    for pattern in [
        "o 1_eye",
        "L 1_nose",
        "m 1_mouth",
        "sdfg 1_keys",
    ]:
        hd1.insert(pattern)

    hd2 = Hydraseq('2_')
    for pattern in [
        "1_eye 1_eye 2_eyes",
        "1_nose 2_nose",
        "1_mouth 2_mouth",
        "1_keys 1_keys 1_keys 2_row"
    ]:
        hd2.insert(pattern)

    hd3 = Hydraseq('3_')
    for pattern in [
        "2_eyes 2_nose 2_mouth 3_face",
        "2_row 3_homerow"
    ]:
        hd3.insert(pattern)

    hd0 = Hydraseq("_")
    hd0.insert("x x o o L m end sdfg sdfg sdfg _period") # NB: the last entry has to be a next_node, i.e. _x
    thoughts = think([hd0, hd1, hd2, hd3])

    assert thoughts == [
        [
            [
                [0, 1, ['x']],
                [1, 2, ['x']],
                [2, 3, ['o']],
                [3, 4, ['o']],
                [4, 5, ['L']],
                [5, 6, ['m']],
                [6, 7, ['end']],
                [7, 8, ['sdfg']],
                [8, 9, ['sdfg']],
                [9, 10, ['sdfg']]
            ]
        ],
        [
            [
                [2, 3, ['1_eye']],
                [3, 4, ['1_eye']],
                [4, 5, ['1_nose']],
                [5, 6, ['1_mouth']]
            ],
            [
                [7, 8, ['1_keys']],
                [8, 9, ['1_keys']],
                [9, 10, ['1_keys']]
            ]
        ],
        [
            [
                [0, 2, ['2_eyes']],
                [2, 3, ['2_nose']],
                [3, 4, ['2_mouth']]
            ],
            [
                [0, 3, ['2_row']]
            ]
        ],
        [
            [
                [0, 3, ['3_face']]
            ],
            [
                [0, 1, ['3_homerow']]
            ]
        ]
    ]

def test_single_layer_recursive():
    """This is test is a negative test, in the sense that it shows that recursive won't work right out of the box.
        More importantly, it shows there is a distinction to be dealt with next predicted, versus next as in 'isa'
        The 'eyes nose mouth' sequence 'isa' face, for example, but 'eyes nose' predict a 'mouth', not 'isa' mouth.
        The distinction causes noise when you recurse.  This is solved by the layer approach because in this case
        'eyes nose mouth' would be in a lower layer pointing to face in the next, while 'eyes nose' point to 'mouth'
        but in the SAME layer, as a predicted value not as identification.
    """
    hd0 = Hydraseq('_')
    for pattern in [
        "x _null",
        "o _eye",
        "L _nose",
        "m _mouth",
        "sdfg _keys",
        "_eye _eye _eyes",
        "_nose _nose",
        "_mouth _mouth",
        "_keys _keys _keys _row",
        "_eyes _nose _mouth _face",
        "_row _homerow",
        "_face _face",
    ]:
        hd0.insert(pattern)
    hdS = Hydraseq('_')
    hdS.insert("o o L m x x _y") # NB: the last entry has to be a next_node, i.e. _x
    thoughts = think([hdS, hd0, hd0, hd0, hd0])

    assert thoughts == \
        [[[[0, 1, ['o']],
           [1, 2, ['o']],
           [2, 3, ['L']],
           [3, 4, ['m']],
           [4, 5, ['x']],
           [5, 6, ['x']]]],
         [[[0, 1, ['_eye']],
           [1, 2, ['_eye']],
           [2, 3, ['_nose']],
           [3, 4, ['_mouth']],
           [4, 5, ['_null']],
           [5, 6, ['_null']]]],
         [[[0, 2, ['_eyes']], [2, 3, ['_nose']], [3, 4, ['_mouth']]],
          [[0, 1, ['_eye']], [1, 2, ['_eye']], [2, 3, ['_nose']], [3, 4, ['_mouth']]]],
         [[[0, 3, ['_face']]],
          [[0, 2, ['_mouth']], [2, 3, ['_mouth']]],
          [[0, 1, ['_nose']], [1, 2, ['_nose']], [2, 3, ['_mouth']]],
          [[0, 2, ['_eyes']], [2, 3, ['_nose']], [3, 4, ['_mouth']]],
          [[0, 1, ['_eye']], [1, 2, ['_eye']], [2, 3, ['_nose']], [3, 4, ['_mouth']]]],
         [[[0, 1, ['_face']]],
          [[0, 1, ['_mouth']], [1, 2, ['_mouth']]],
          [[0, 1, ['_nose']], [1, 2, ['_nose']], [2, 3, ['_mouth']]],
          [[0, 3, ['_face']]],
          [[0, 2, ['_mouth']], [2, 3, ['_mouth']]],
          [[0, 1, ['_nose']], [1, 2, ['_nose']], [2, 3, ['_mouth']]],
          [[0, 2, ['_eyes']], [2, 3, ['_nose']], [3, 4, ['_mouth']]],
          [[0, 1, ['_eye']], [1, 2, ['_eye']], [2, 3, ['_nose']], [3, 4, ['_mouth']]]]]

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


def test_shapes_cortex_face():
    cortex = shapes.cortex
    hys = Hydraseq("_")
    cortex[0].insert(hys.get_word_array(shapes.face))

    assert think(cortex)[-1][0][0][2] == ['2_FACE']

def test_shapes_cortex_face_spaced():
    cortex = shapes.cortex
    hys = Hydraseq("_")
    cortex[0] = Hydraseq("_")
    cortex[0].insert(hys.get_word_array(shapes.face_spaced))

    assert think(cortex)[2] == [[[0, 2, ['1_eyes']]], [[0, 1, ['1_nose']]], [[0, 3, ['1_mouth']]]]
