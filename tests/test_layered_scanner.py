"""
Experiment: two-level LayeredScanner using a toy fruit/modifier domain.

Level 1 — raw tokens -> spans:
    SIZE COLOR -> MODIFIER   ("big red")
    COLOR      -> MODIFIER   ("red")
    SIZE       -> MODIFIER   ("big")
    FRUIT      -> FRUIT_SPAN ("apple")

Level 2 — Level 1 labels -> concept:
    MODIFIER FRUIT_SPAN -> ITEM
    FRUIT_SPAN          -> ITEM   (bare fruit, no modifier)

So "big red apple" flows:
    raw:     [big]    [red]    [apple]
    level1:  SIZE     COLOR    FRUIT
             └── MODIFIER ──┘  └─ FRUIT_SPAN ─┘
    level2:  MODIFIER          FRUIT_SPAN
             └───────── ITEM ──────────────┘
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, PatternScanner, LayeredScanner


SIZES   = {'big', 'small', 'large', 'tiny'}
COLORS  = {'red', 'green', 'blue', 'yellow'}
FRUITS  = {'apple', 'grape', 'mango', 'banana'}


def level1_encoder(token):
    cats = []
    if token in SIZES:  cats.append('SIZE')
    if token in COLORS: cats.append('COLOR')
    if token in FRUITS: cats.append('FRUIT')
    return cats or ['UNKNOWN']


def level2_encoder(token):
    return [token]          # labels from level 1 pass through unchanged


def make_level1_scanner():
    hdr = Hydraseq('l1')
    hdr.insert([['SIZE'], ['COLOR'], ['MODIFIER']])
    hdr.insert([['COLOR'],           ['MODIFIER']])
    hdr.insert([['SIZE'],            ['MODIFIER']])
    hdr.insert([['FRUIT'],           ['FRUIT_SPAN']])
    return PatternScanner(hdr, level1_encoder)


def make_level2_scanner():
    hdr = Hydraseq('l2')
    hdr.insert([['MODIFIER'],  ['FRUIT_SPAN'], ['ITEM']])
    hdr.insert([['FRUIT_SPAN'],                ['ITEM']])
    return PatternScanner(hdr, level2_encoder)


def make_layered():
    return LayeredScanner(
        layers=[make_level1_scanner(), make_level2_scanner()],
        intermediate_targets=[['MODIFIER', 'FRUIT_SPAN']]
    )


# --- level 1 in isolation ---

def test_l1_size_color_gives_modifier():
    s = make_level1_scanner()
    markers = s.get_markers(['big', 'red'], ['MODIFIER'])
    assert any(m.text == 'big red' for m in markers)

def test_l1_color_alone_gives_modifier():
    s = make_level1_scanner()
    markers = s.get_markers(['red'], ['MODIFIER'])
    assert any(m.text == 'red' for m in markers)

def test_l1_fruit_gives_fruit_span():
    s = make_level1_scanner()
    markers = s.get_markers(['apple'], ['FRUIT_SPAN'])
    assert any(m.text == 'apple' for m in markers)


# --- level 2 in isolation ---

def test_l2_modifier_fruit_span_gives_item():
    s = make_level2_scanner()
    markers = s.get_markers(['MODIFIER', 'FRUIT_SPAN'], ['ITEM'])
    assert any(m.text == 'MODIFIER FRUIT_SPAN' for m in markers)

def test_l2_bare_fruit_span_gives_item():
    s = make_level2_scanner()
    markers = s.get_markers(['FRUIT_SPAN'], ['ITEM'])
    assert any(m.text == 'FRUIT_SPAN' for m in markers)


# --- layered: full pipeline ---

def test_layered_size_color_fruit():
    ls = make_layered()
    result = ls.scan('big red apple', ['ITEM'])
    assert len(result) > 0
    assert result[0].labels == ['ITEM']

def test_layered_color_fruit():
    ls = make_layered()
    result = ls.scan('red apple', ['ITEM'])
    assert len(result) > 0

def test_layered_size_fruit():
    ls = make_layered()
    result = ls.scan('small grape', ['ITEM'])
    assert len(result) > 0

def test_layered_bare_fruit():
    ls = make_layered()
    result = ls.scan('mango', ['ITEM'])
    assert len(result) > 0

def test_layered_no_fruit_returns_empty():
    ls = make_layered()
    result = ls.scan('big red', ['ITEM'])
    assert result == []

def test_layered_unknown_tokens_return_empty():
    ls = make_layered()
    result = ls.scan('the quick brown fox', ['ITEM'])
    assert result == []
