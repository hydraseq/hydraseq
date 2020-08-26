import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq

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

def test_hydra_depths():
    hdr = Hydraseq('main')

    assert len(hdr.d_depths) == 0, "Initially a hydraseq should have no depth sets"
    st = "one two three four five six seven eight nine ten"
    hdr.insert(st)
    assert len(hdr.d_depths) == 10, "there should be one set per depht traversed"
    st_lst = st.split()
    for idx, set_item in hdr.d_depths.items():
        assert len(hdr.d_depths[idx]) == 1, "there should be one item in each depth level"
        assert next(node for node in hdr.d_depths[idx]).key == st_lst[idx-1], "the nodes should be in depth order"

    hdr.look_ahead("one two three four five six seven eight nine")
    last_node = next(node for node in hdr.next_nodes)
    assert last_node.depth == 10

    hdr.insert("one two three four five six siete ocho nueve diez")
    hdr.insert("one two three four five six siete ocho nueve")
    last_node = next(node for node in hdr.next_nodes)
    assert last_node.depth == 10

    hdr.insert("one two three four five six siete")
    last_node = next(node for node in hdr.next_nodes)
    assert last_node.depth == 8


def test_activate_node_pathway():
    hdr = Hydraseq('main')

    hdr.insert("a b c d e f LETTERS")
    hdr.insert("1 2 3 4 5 6 NUMBERS")
    hdr.insert("a1 2b b4 MIXED")

    hdr.activate_node_pathway('LETTERS')

    assert {node.key for node in hdr.path_nodes} == {"a", "b", "c", "d", "e", "f", "LETTERS"}
    assert hdr.look_ahead("a b c d").get_active_values() == ["d"]
    assert hdr.look_ahead("a b c d").get_next_values() == ["e"]
    assert {node.key for node in hdr.path_nodes} == {"a", "b", "c", "d", "e", "f", "LETTERS"}
    assert hdr.look_ahead("1 2 3 4").get_active_values() == []
    assert hdr.look_ahead("1 2 3 4").get_next_values() == []

    hdr.reset_node_pathway()
    assert {node.key for node in hdr.path_nodes} == set()
    assert hdr.look_ahead("a b c d").get_active_values() == ["d"]
    assert hdr.look_ahead("a b c d").get_next_values() == ["e"]
    assert {node.key for node in hdr.path_nodes} == set()
    assert hdr.look_ahead("1 2 3 4").get_active_values() == ["4"]
    assert hdr.look_ahead("1 2 3 4").get_next_values() == ["5"]

def test_active_synapses():
    hdr = Hydraseq('main')

    hdr.insert("a b c d e f")
    hdr.insert("1 2 3 4 5 6")

    assert hdr.look_ahead("a b c d e").get_active_values() == ['e']
    assert hdr.look_ahead("1 2 3 4 5").get_active_values() == ['5']

    hdr.set_active_synapses(['f'])

    assert hdr.look_ahead("a b c d e").get_active_values() == ['e']
    assert hdr.look_ahead("1 2 3 4 5").get_active_values() == []
    assert hdr.look_ahead("a b c d").get_active_values() == ['d']

    hdr.reset_active_synapses()

    assert hdr.look_ahead("a b c d e").get_active_values() == ['e']
    assert hdr.look_ahead("1 2 3 4 5").get_active_values() == ['5']
    assert hdr.look_ahead("a b c d").get_active_values() == ['d']


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


def test_run_convolutions_json():
    hdr = Hydraseq('_')

    hdr.insert("a b c _ALPHA")
    hdr.insert("1 2 3 _DIGIT")

    assert hdr.convolutions("a b c 1 2 3".split()) == [
        {'convo': '_ALPHA', 'end': 3, 'start': 0, 'words': ['a', 'b', 'c']},
        {'convo': '_DIGIT', 'end': 6, 'start': 3, 'words': ['1', '2', '3']}
    ]
    assert hdr.convolutions("a b 1 2 3 a b".split()) == [
        {'convo': '_DIGIT', 'end': 5, 'start': 2, 'words': ['1', '2', '3']}
    ]

def test_run_convolutions_overlap():
    hdr = Hydraseq('_')

    hdr.insert("b a d _1")
    hdr.insert("a n d _2")
    hdr.insert("a d a _3")
    hdr.insert("a n d y _4")
    hdr.insert("a d a n _5")

    tester = "b a d a n d y".split()

    assert hdr.convolutions(tester) == [
        {'convo': '_1', 'end': 3, 'start': 0, 'words': ['b', 'a', 'd']},
        {'convo': '_3', 'end': 4, 'start': 1, 'words': ['a', 'd', 'a']},
        {'convo': '_5', 'end': 5, 'start': 1, 'words': ['a', 'd', 'a', 'n']},
        {'convo': '_2', 'end': 6, 'start': 3, 'words': ['a', 'n', 'd']},
        {'convo': '_4', 'end': 7, 'start': 3, 'words': ['a', 'n', 'd', 'y']}
    ]

def test_get_downwards():
    hds = Hydraseq("_")

    hds.insert("a b c _D")
    hds.insert("e f g _D")
    hds.insert("c e f _D")

    assert hds.get_downwards(["_D"]) == ['a', 'b', 'c', 'e', 'f', 'g']



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

