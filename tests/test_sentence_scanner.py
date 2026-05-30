"""
Experiment: 3-layer sentence recognizer using LayeredScanner.

Layer 1 (lexical):   raw words  -> POS tags  (PROPN, NOUN, VERB, DET, ADJ)
Layer 2 (syntactic): POS tags   -> phrases   (NP, VP)
Layer 3 (semantic):  phrases    -> sentence  (SENTENCE)

Example trace for "alice reads the big book":
    Layer 1: alice->PROPN  reads->VERB  the->DET  big->ADJ  book->NOUN
    Layer 2: PROPN->NP  VERB->VP  DET ADJ NOUN->NP
    Layer 3: NP VP NP -> SENTENCE

Vocabulary:
    Proper nouns:  alice, bob, carol
    Common nouns:  book, ball, cat
    Verbs:         reads, throws, chases, sees
    Determiners:   the, a
    Adjectives:    big, small, red, quick
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, PatternScanner, LayeredScanner

L1_TARGETS = ['PROPN', 'NOUN', 'VERB', 'DET', 'ADJ']
L2_TARGETS = ['NP', 'VP']

PROPNS = ['alice', 'bob', 'carol']
NOUNS  = ['book', 'ball', 'cat']
VERBS  = ['reads', 'throws', 'chases', 'sees']
DETS   = ['the', 'a']
ADJS   = ['big', 'small', 'red', 'quick']


def make_l1_scanner():
    """Lexical layer: each word maps to its POS tag via a 2-token sequence."""
    hdr = Hydraseq('l1')
    for w in PROPNS: hdr.insert([[w], ['PROPN']])
    for w in NOUNS:  hdr.insert([[w], ['NOUN']])
    for w in VERBS:  hdr.insert([[w], ['VERB']])
    for w in DETS:   hdr.insert([[w], ['DET']])
    for w in ADJS:   hdr.insert([[w], ['ADJ']])
    return PatternScanner(hdr, lambda token: [token])


def make_l2_scanner():
    """Syntactic layer: POS tag sequences -> phrase types."""
    hdr = Hydraseq('l2')
    hdr.insert([['PROPN'],                    ['NP']])
    hdr.insert([['NOUN'],                     ['NP']])
    hdr.insert([['DET'],  ['NOUN'],           ['NP']])
    hdr.insert([['DET'],  ['ADJ'], ['NOUN'],  ['NP']])
    hdr.insert([['VERB'],                     ['VP']])
    return PatternScanner(hdr, lambda token: [token])


def make_l3_scanner():
    """Semantic layer: phrase sequences -> sentence patterns."""
    hdr = Hydraseq('l3')
    hdr.insert([['NP'], ['VP'], ['NP'], ['SENTENCE']])  # subject verb object
    hdr.insert([['NP'], ['VP'],         ['SENTENCE']])  # subject verb (intransitive)
    return PatternScanner(hdr, lambda token: [token])


def make_sentence_scanner():
    return LayeredScanner(
        layers=[make_l1_scanner(), make_l2_scanner(), make_l3_scanner()],
        intermediate_targets=[L1_TARGETS, L2_TARGETS]
    )


# --- layer 1: lexical tagging ---

def test_l1_tags_proper_noun():
    s = make_l1_scanner()
    markers = s.get_markers(['alice'], L1_TARGETS)
    assert any(m.labels == ['PROPN'] and m.text == 'alice' for m in markers)

def test_l1_tags_verb():
    s = make_l1_scanner()
    markers = s.get_markers(['chases'], L1_TARGETS)
    assert any(m.labels == ['VERB'] for m in markers)

def test_l1_tags_all_words_in_sentence():
    s = make_l1_scanner()
    markers = s.get_markers(['the', 'big', 'book'], L1_TARGETS)
    labels = {m.labels[0] for m in markers if m.length == 1}
    assert 'DET' in labels
    assert 'ADJ' in labels
    assert 'NOUN' in labels


# --- layer 2: phrase recognition ---

def test_l2_propn_gives_np():
    s = make_l2_scanner()
    markers = s.get_markers(['PROPN'], L2_TARGETS)
    assert any(m.labels == ['NP'] for m in markers)

def test_l2_det_noun_gives_np():
    s = make_l2_scanner()
    markers = s.get_markers(['DET', 'NOUN'], L2_TARGETS)
    assert any(m.labels == ['NP'] and m.text == 'DET NOUN' for m in markers)

def test_l2_det_adj_noun_gives_np():
    s = make_l2_scanner()
    markers = s.get_markers(['DET', 'ADJ', 'NOUN'], L2_TARGETS)
    assert any(m.labels == ['NP'] and m.text == 'DET ADJ NOUN' for m in markers)

def test_l2_verb_gives_vp():
    s = make_l2_scanner()
    markers = s.get_markers(['VERB'], L2_TARGETS)
    assert any(m.labels == ['VP'] for m in markers)


# --- layer 3: sentence recognition ---

def test_l3_np_vp_np_gives_sentence():
    s = make_l3_scanner()
    markers = s.get_markers(['NP', 'VP', 'NP'], ['SENTENCE'])
    assert any(m.labels == ['SENTENCE'] for m in markers)

def test_l3_np_vp_gives_sentence():
    s = make_l3_scanner()
    markers = s.get_markers(['NP', 'VP'], ['SENTENCE'])
    assert any(m.labels == ['SENTENCE'] for m in markers)

def test_l3_vp_np_alone_is_not_sentence():
    s = make_l3_scanner()
    markers = s.get_markers(['VP', 'NP'], ['SENTENCE'])
    assert markers == []


# --- full 3-layer stack ---

def test_sentence_svo_proper_nouns():
    # alice chases bob
    ls = make_sentence_scanner()
    result = ls.scan('alice chases bob', ['SENTENCE'])
    assert len(result) > 0

def test_sentence_svo_with_det_noun():
    # alice reads the book
    ls = make_sentence_scanner()
    result = ls.scan('alice reads the book', ['SENTENCE'])
    assert len(result) > 0

def test_sentence_svo_with_det_adj_noun():
    # alice reads the big book
    ls = make_sentence_scanner()
    result = ls.scan('alice reads the big book', ['SENTENCE'])
    assert len(result) > 0

def test_sentence_sv_intransitive():
    # bob reads  (no object)
    ls = make_sentence_scanner()
    result = ls.scan('bob reads', ['SENTENCE'])
    assert len(result) > 0

def test_sentence_det_noun_subject():
    # the cat chases bob
    ls = make_sentence_scanner()
    result = ls.scan('the cat chases bob', ['SENTENCE'])
    assert len(result) > 0

def test_sentence_wrong_order_is_not_sentence():
    # verb first — not a valid sentence pattern
    ls = make_sentence_scanner()
    result = ls.scan('chases alice bob', ['SENTENCE'])
    assert result == []

def test_sentence_unknown_words_return_empty():
    ls = make_sentence_scanner()
    result = ls.scan('the quick brown fox', ['SENTENCE'])
    assert result == []
