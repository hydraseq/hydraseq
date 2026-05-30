"""
Tests for PatternScanner using a toy domain:
  - tokens are categorized as COLOR, SIZE, or FRUIT
  - patterns like SIZE COLOR FRUIT -> ITEM are trained into a Hydraseq
  - scanner finds matching spans in a sentence
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, PatternScanner

COLORS = {'red', 'green', 'blue', 'yellow'}
SIZES  = {'big', 'small', 'tiny', 'large'}
FRUITS = {'apple', 'banana', 'grape', 'mango'}

def encoder(token):
    token = token.lower()
    categories = []
    if token in COLORS: categories.append('COLOR')
    if token in SIZES:  categories.append('SIZE')
    if token in FRUITS: categories.append('FRUIT')
    if not categories:  categories.append('OTHER')
    return categories


def make_scanner():
    seq = Hydraseq('items')
    # SIZE COLOR FRUIT -> ITEM
    seq.insert([['SIZE'], ['COLOR'], ['FRUIT'], ['ITEM']])
    # COLOR FRUIT -> ITEM  (no size)
    seq.insert([['COLOR'], ['FRUIT'], ['ITEM']])
    # SIZE FRUIT -> ITEM  (no color)
    seq.insert([['SIZE'], ['FRUIT'], ['ITEM']])
    return PatternScanner(seq, encoder)


# --- get_markers ---

def test_markers_full_pattern():
    scanner = make_scanner()
    markers = scanner.get_markers("big red apple", ['ITEM'])
    # both 'big red apple' and sub-span 'red apple' match — check the full span is present
    texts = [m.text for m in markers]
    assert 'big red apple' in texts
    full = next(m for m in markers if m.text == 'big red apple')
    assert full.start == 0 and full.end == 3

def test_markers_partial_pattern_color_fruit():
    scanner = make_scanner()
    markers = scanner.get_markers("red apple", ['ITEM'])
    assert len(markers) == 1
    assert markers[0].text == 'red apple'

def test_markers_partial_pattern_size_fruit():
    scanner = make_scanner()
    markers = scanner.get_markers("small banana", ['ITEM'])
    assert len(markers) == 1
    assert markers[0].text == 'small banana'

def test_markers_no_match():
    scanner = make_scanner()
    markers = scanner.get_markers("the quick brown fox", ['ITEM'])
    assert markers == []

def test_markers_finds_span_within_sentence():
    scanner = make_scanner()
    # pattern is embedded mid-sentence
    markers = scanner.get_markers("i bought big red apple yesterday", ['ITEM'])
    assert any(m.text == 'big red apple' for m in markers)

def test_markers_multiple_spans():
    scanner = make_scanner()
    # two separate patterns in one sentence
    markers = scanner.get_markers("big red apple small green grape", ['ITEM'])
    texts = [m.text for m in markers]
    assert any('big red apple' in t for t in texts)
    assert any('small green grape' in t for t in texts)


# --- get_paths ---

def test_paths_single_span():
    scanner = make_scanner()
    markers = scanner.get_markers("big red apple", ['ITEM'])
    paths = scanner.get_paths(markers)
    assert len(paths) >= 1
    assert any(len(p) == 1 and p[0].text == 'big red apple' for p in paths)

def test_paths_chains_adjacent_spans():
    scanner = make_scanner()
    markers = scanner.get_markers("big red apple small green grape", ['ITEM'])
    paths = scanner.get_paths(markers)
    # should find at least one path that includes both full items tiling end-to-end
    all_texts = [tuple(m.text for m in p) for p in paths]
    assert any('big red apple' in ts and 'small green grape' in ts for ts in all_texts)


# --- tokenizer override ---

def test_custom_tokenizer():
    scanner = make_scanner()
    # supply pre-tokenized list instead of string
    tokens = ['big', 'red', 'apple']
    markers = scanner.get_markers(tokens, ['ITEM'])
    texts = [m.text for m in markers]
    assert 'big red apple' in texts
