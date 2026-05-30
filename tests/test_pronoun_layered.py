"""
Experiment: pronoun resolution within the LayeredScanner framework.

Sentence: "alice throws the ball IT bounces"

IT is ambiguous — it could refer to alice (ANIMATE/PROPN) or ball (INANIMATE/NOUN).
Both bindings produce a valid sentence at Layer 3 (structural ambiguity is genuinely held).
A semantic layer resolves it: only INANIMATE things bounce coherently.

This experiment also exposes a gap in LayeredScanner: currently it takes labels[0]
when passing a marker's labels to the next layer, which drops the ambiguity.
Multi-label markers need to fan out into parallel interpretations.

Layers:
    Layer 1 (lexical):   words      -> POS tags (PROPN, NOUN, VERB, DET, ADJ)
                         IT         -> PROPN | NOUN  (ambiguous)
    Layer 2 (syntactic): POS tags   -> phrases (NP, VP)
    Layer 3 (structural): phrases   -> SENTENCE

    Semantic resolver (separate):
        ANIMATE   + bounces -> INCOHERENT
        INANIMATE + bounces -> COHERENT
        -> IT must be INANIMATE -> refers to ball
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, PatternScanner, LayeredScanner

# --- vocabulary ---

PROPNS    = ['alice', 'bob', 'carol']
NOUNS     = ['book', 'ball', 'cat']
VERBS     = ['reads', 'throws', 'chases', 'sees', 'bounces']
DETS      = ['the', 'a']
ADJS      = ['big', 'small', 'red', 'quick']

ANIMATES   = {'alice', 'bob', 'carol', 'cat'}
INANIMATES = {'book', 'ball'}

L1_TARGETS = ['PROPN', 'NOUN', 'VERB', 'DET', 'ADJ']
L2_TARGETS = ['NP', 'VP']


def make_l1_scanner():
    hdr = Hydraseq('l1')
    for w in PROPNS: hdr.insert([[w], ['PROPN']])
    for w in NOUNS:  hdr.insert([[w], ['NOUN']])
    for w in VERBS:  hdr.insert([[w], ['VERB']])
    for w in DETS:   hdr.insert([[w], ['DET']])
    for w in ADJS:   hdr.insert([[w], ['ADJ']])
    # IT is ambiguous: both PROPN and NOUN are valid
    hdr.insert([['IT'], ['PROPN']])
    hdr.insert([['IT'], ['NOUN']])
    return PatternScanner(hdr, lambda token: [token])


def make_l2_scanner():
    hdr = Hydraseq('l2')
    hdr.insert([['PROPN'],                   ['NP']])
    hdr.insert([['NOUN'],                    ['NP']])
    hdr.insert([['DET'],  ['NOUN'],          ['NP']])
    hdr.insert([['DET'],  ['ADJ'], ['NOUN'], ['NP']])
    hdr.insert([['VERB'],                    ['VP']])
    return PatternScanner(hdr, lambda token: [token])


def make_l3_scanner():
    hdr = Hydraseq('l3')
    hdr.insert([['NP'], ['VP'], ['NP'], ['SENTENCE']])
    hdr.insert([['NP'], ['VP'],         ['SENTENCE']])
    return PatternScanner(hdr, lambda token: [token])


def make_sentence_scanner():
    return LayeredScanner(
        layers=[make_l1_scanner(), make_l2_scanner(), make_l3_scanner()],
        intermediate_targets=[L1_TARGETS, L2_TARGETS]
    )


def make_semantic_resolver():
    """A Hydraseq trained on verb-subject semantic compatibility."""
    hdr = Hydraseq('semantic')
    # animate subjects
    for verb in ['throws', 'sees', 'reads', 'chases']:
        hdr.insert([['ANIMATE'], [verb], ['COHERENT']])
    hdr.insert([['ANIMATE'], ['bounces'], ['INCOHERENT']])
    # inanimate subjects
    hdr.insert([['INANIMATE'], ['bounces'], ['COHERENT']])
    hdr.insert([['INANIMATE'], ['falls'],   ['COHERENT']])
    for verb in ['throws', 'sees', 'reads', 'chases']:
        hdr.insert([['INANIMATE'], [verb], ['INCOHERENT']])
    return hdr


def semantic_encoder(token):
    """Maps words to ANIMATE/INANIMATE. IT is ambiguous — encodes as both."""
    if token in ANIMATES:   return ['ANIMATE']
    if token in INANIMATES: return ['INANIMATE']
    if token == 'IT':       return ['ANIMATE', 'INANIMATE']
    return [token]          # verbs pass through as-is


# --- Layer 1: IT holds ambiguity ---

def test_IT_encodes_as_both_propn_and_noun():
    s = make_l1_scanner()
    markers = s.get_markers(['IT'], L1_TARGETS)
    all_labels = {label for m in markers for label in m.labels}
    assert 'PROPN' in all_labels
    assert 'NOUN' in all_labels

def test_IT_marker_has_multiple_labels():
    """IT produces a single marker with both labels — the held ambiguity."""
    s = make_l1_scanner()
    markers = s.get_markers(['IT'], L1_TARGETS)
    # one marker, two labels
    assert len(markers) == 1
    assert set(markers[0].labels) == {'PROPN', 'NOUN'}


# --- Both bindings produce valid sentences structurally ---

def test_IT_as_propn_gives_valid_sentence():
    """Force IT=PROPN: 'IT bounces' is a valid sentence."""
    l2 = make_l2_scanner()
    l3 = make_l3_scanner()
    # PROPN -> NP, VERB -> VP
    np_markers = l2.get_markers(['PROPN'], L2_TARGETS)
    vp_markers = l2.get_markers(['VERB'], L2_TARGETS)
    assert any(m.labels == ['NP'] for m in np_markers)
    assert any(m.labels == ['VP'] for m in vp_markers)
    # NP VP -> SENTENCE
    result = l3.get_markers(['NP', 'VP'], ['SENTENCE'])
    assert any(m.labels == ['SENTENCE'] for m in result)

def test_IT_as_noun_gives_valid_sentence():
    """Force IT=NOUN: 'IT bounces' is also a valid sentence."""
    l2 = make_l2_scanner()
    l3 = make_l3_scanner()
    # NOUN -> NP, VERB -> VP
    np_markers = l2.get_markers(['NOUN'], L2_TARGETS)
    assert any(m.labels == ['NP'] for m in np_markers)
    # same NP VP -> SENTENCE path
    result = l3.get_markers(['NP', 'VP'], ['SENTENCE'])
    assert any(m.labels == ['SENTENCE'] for m in result)


# --- Semantic resolution ---

def test_animate_bounces_is_incoherent():
    hdr = make_semantic_resolver()
    result = hdr.look_ahead([['ANIMATE'], ['bounces']]).get_next_values()
    assert 'INCOHERENT' in result
    assert 'COHERENT' not in result

def test_inanimate_bounces_is_coherent():
    hdr = make_semantic_resolver()
    result = hdr.look_ahead([['INANIMATE'], ['bounces']]).get_next_values()
    assert 'COHERENT' in result
    assert 'INCOHERENT' not in result

def test_IT_bounces_holds_both_outcomes():
    """IT encodes as ['ANIMATE','INANIMATE'] — both outcomes predicted simultaneously."""
    hdr = make_semantic_resolver()
    result = hdr.look_ahead([semantic_encoder('IT'), ['bounces']]).get_next_values()
    assert 'COHERENT' in result
    assert 'INCOHERENT' in result

def test_semantic_resolution_selects_inanimate():
    """Filtering for COHERENT uniquely selects the INANIMATE binding -> ball."""
    hdr = make_semantic_resolver()
    resolved = []
    for candidate, label in [('alice', 'ANIMATE'), ('ball', 'INANIMATE')]:
        result = hdr.look_ahead([[label], ['bounces']]).get_next_values()
        if 'COHERENT' in result:
            resolved.append(candidate)
    assert resolved == ['ball']

def test_semantic_resolution_flips_for_throws():
    """For 'throws', the ANIMATE binding is coherent — resolves to alice."""
    hdr = make_semantic_resolver()
    resolved = []
    for candidate, label in [('alice', 'ANIMATE'), ('ball', 'INANIMATE')]:
        result = hdr.look_ahead([[label], ['throws']]).get_next_values()
        if 'COHERENT' in result:
            resolved.append(candidate)
    assert resolved == ['alice']


# --- The gap: LayeredScanner drops ambiguity at label handoff ---

def test_layered_scanner_fans_out_both_bindings():
    """
    After the fan-out fix, LayeredScanner carries both IT=PROPN and IT=NOUN
    interpretations through all structural layers simultaneously.
    scan() returns one SENTENCE result per surviving interpretation.
    """
    ls = make_sentence_scanner()
    result = ls.scan(['IT', 'bounces'], ['SENTENCE'])
    # both bindings produce a valid SENTENCE — ambiguity genuinely preserved
    assert len(result) == 2
    assert all(m.labels == ['SENTENCE'] for m in result)

def test_semantic_resolution_after_fan_out():
    """
    With both interpretations returning SENTENCE, the semantic resolver
    can now correctly pick the coherent one: IT=INANIMATE (ball), not ANIMATE.
    This is the full pipeline working end-to-end.
    """
    ls = make_sentence_scanner()
    hdr_sem = make_semantic_resolver()

    # structural layer: both bindings survive
    result = ls.scan(['IT', 'bounces'], ['SENTENCE'])
    assert len(result) == 2

    # semantic layer: only INANIMATE bounces coherently
    resolved = []
    for candidate, label in [('alice', 'ANIMATE'), ('ball', 'INANIMATE')]:
        sem_result = hdr_sem.look_ahead([[label], ['bounces']]).get_next_values()
        if 'COHERENT' in sem_result:
            resolved.append(candidate)

    assert resolved == ['ball']
