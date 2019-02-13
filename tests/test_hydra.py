import re
import sys
sys.path.append('./hydraseq')
from hydra import Hydra

def test_hydra():
    words = ['every', 'good', 'boy', 'does', 'fine', 'everything']

    hh = Hydra(words)

    for idx, word in enumerate(words):
        hh.insert_word(word, idx)
        hh.insert_word(word, idx*2)
        assert hh.lookup(word) == set([idx, idx*2])

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

