"""
Closed-loop pronoun resolution: semantic coherence baked into Layer 3 training.

The key insight: instead of a separate semantic resolver AFTER the structural
layers, Layer 3 is trained ONLY on coherent subject-verb-object combinations.
Incoherent bindings fail to produce SENTENCE at Layer 3 — eliminated by the
structure itself, not by external code.

Layer 1 (lexical-semantic): words -> semantically-typed POS tags
    alice/bob/carol -> ANIMATE_PROPN
    cat             -> ANIMATE_NOUN
    book/ball       -> INANIMATE_NOUN
    reads/throws/chases/sees -> ANIMATE_VERB  (needs animate subject)
    bounces/falls   -> INANIMATE_VERB         (needs inanimate subject)
    IT              -> ANIMATE_PROPN | INANIMATE_NOUN  (ambiguous — fan-out)

Layer 2 (phrase): semantically-typed POS -> semantically-typed phrases
    ANIMATE_PROPN/NOUN -> ANIMATE_NP
    INANIMATE_NOUN     -> INANIMATE_NP
    ANIMATE_VERB       -> ANIMATE_VP
    INANIMATE_VERB     -> INANIMATE_VP

Layer 3 (coherent sentences only — this IS the semantic resolver):
    ANIMATE_NP   ANIMATE_VP                -> SENTENCE  (alice reads)
    ANIMATE_NP   ANIMATE_VP   ANIMATE_NP   -> SENTENCE  (alice chases bob)
    ANIMATE_NP   ANIMATE_VP   INANIMATE_NP -> SENTENCE  (alice throws the ball)
    INANIMATE_NP INANIMATE_VP              -> SENTENCE  (the ball bounces)
    (incoherent combos not trained -> no SENTENCE)

Trace for "IT bounces":
    Fan-out: ANIMATE_PROPN INANIMATE_VERB  -> ANIMATE_NP INANIMATE_VP  -> NOT trained -> eliminated
           | INANIMATE_NOUN INANIMATE_VERB -> INANIMATE_NP INANIMATE_VP -> SENTENCE ✓

Result: 1 SENTENCE. IT resolved to INANIMATE (ball). No external code needed.
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, PatternScanner, LayeredScanner

L1_TARGETS = ['ANIMATE_PROPN', 'ANIMATE_NOUN', 'INANIMATE_NOUN',
              'ANIMATE_VERB', 'INANIMATE_VERB', 'DET', 'ADJ']
L2_TARGETS = ['ANIMATE_NP', 'INANIMATE_NP', 'ANIMATE_VP', 'INANIMATE_VP']


def make_l1():
    hdr = Hydraseq('l1')
    for w in ['alice', 'bob', 'carol']:  hdr.insert([[w], ['ANIMATE_PROPN']])
    for w in ['cat']:                    hdr.insert([[w], ['ANIMATE_NOUN']])
    for w in ['book', 'ball']:           hdr.insert([[w], ['INANIMATE_NOUN']])
    for w in ['reads', 'throws', 'chases', 'sees']:
                                         hdr.insert([[w], ['ANIMATE_VERB']])
    for w in ['bounces', 'falls']:       hdr.insert([[w], ['INANIMATE_VERB']])
    for w in ['the', 'a']:              hdr.insert([[w], ['DET']])
    for w in ['big', 'small', 'red']:   hdr.insert([[w], ['ADJ']])
    # IT is ambiguous: could refer to an animate or inanimate referent
    hdr.insert([['IT'], ['ANIMATE_PROPN']])
    hdr.insert([['IT'], ['INANIMATE_NOUN']])
    return PatternScanner(hdr, lambda token: [token])


def make_l2():
    hdr = Hydraseq('l2')
    hdr.insert([['ANIMATE_PROPN'],                      ['ANIMATE_NP']])
    hdr.insert([['ANIMATE_NOUN'],                       ['ANIMATE_NP']])
    hdr.insert([['DET'], ['ANIMATE_NOUN'],              ['ANIMATE_NP']])
    hdr.insert([['INANIMATE_NOUN'],                     ['INANIMATE_NP']])
    hdr.insert([['DET'], ['INANIMATE_NOUN'],            ['INANIMATE_NP']])
    hdr.insert([['DET'], ['ADJ'], ['INANIMATE_NOUN'],   ['INANIMATE_NP']])
    hdr.insert([['DET'], ['ADJ'], ['ANIMATE_NOUN'],     ['ANIMATE_NP']])
    hdr.insert([['ANIMATE_VERB'],                       ['ANIMATE_VP']])
    hdr.insert([['INANIMATE_VERB'],                     ['INANIMATE_VP']])
    return PatternScanner(hdr, lambda token: [token])


def make_l3():
    """Only coherent subject-verb-object combinations are trained.
    This layer IS the semantic resolver — incoherent combos simply have
    no path to SENTENCE."""
    hdr = Hydraseq('l3')
    hdr.insert([['ANIMATE_NP'],   ['ANIMATE_VP'],                        ['SENTENCE']])
    hdr.insert([['ANIMATE_NP'],   ['ANIMATE_VP'],   ['ANIMATE_NP'],      ['SENTENCE']])
    hdr.insert([['ANIMATE_NP'],   ['ANIMATE_VP'],   ['INANIMATE_NP'],    ['SENTENCE']])
    hdr.insert([['INANIMATE_NP'], ['INANIMATE_VP'],                      ['SENTENCE']])
    return PatternScanner(hdr, lambda token: [token])


def make_scanner():
    return LayeredScanner(
        layers=[make_l1(), make_l2(), make_l3()],
        intermediate_targets=[L1_TARGETS, L2_TARGETS]
    )


# --- layer 1: semantic typing ---

def test_l1_animate_propn():
    s = make_l1()
    markers = s.get_markers(['alice'], L1_TARGETS)
    assert any(m.labels == ['ANIMATE_PROPN'] for m in markers)

def test_l1_inanimate_noun():
    s = make_l1()
    markers = s.get_markers(['ball'], L1_TARGETS)
    assert any(m.labels == ['INANIMATE_NOUN'] for m in markers)

def test_l1_animate_verb():
    s = make_l1()
    markers = s.get_markers(['throws'], L1_TARGETS)
    assert any(m.labels == ['ANIMATE_VERB'] for m in markers)

def test_l1_inanimate_verb():
    s = make_l1()
    markers = s.get_markers(['bounces'], L1_TARGETS)
    assert any(m.labels == ['INANIMATE_VERB'] for m in markers)

def test_l1_IT_is_ambiguous():
    s = make_l1()
    markers = s.get_markers(['IT'], L1_TARGETS)
    assert len(markers) == 1
    assert set(markers[0].labels) == {'ANIMATE_PROPN', 'INANIMATE_NOUN'}


# --- layer 3: only coherent combos produce SENTENCE ---

def test_l3_animate_animate_vp_is_sentence():
    s = make_l3()
    result = s.get_markers(['ANIMATE_NP', 'ANIMATE_VP'], ['SENTENCE'])
    assert len(result) > 0

def test_l3_inanimate_inanimate_vp_is_sentence():
    s = make_l3()
    result = s.get_markers(['INANIMATE_NP', 'INANIMATE_VP'], ['SENTENCE'])
    assert len(result) > 0

def test_l3_animate_inanimate_vp_is_not_sentence():
    """Animate subject with inanimate verb — not trained — no SENTENCE."""
    s = make_l3()
    result = s.get_markers(['ANIMATE_NP', 'INANIMATE_VP'], ['SENTENCE'])
    assert result == []

def test_l3_inanimate_animate_vp_is_not_sentence():
    """Inanimate subject with animate verb — not trained — no SENTENCE."""
    s = make_l3()
    result = s.get_markers(['INANIMATE_NP', 'ANIMATE_VP'], ['SENTENCE'])
    assert result == []


# --- closed-loop disambiguation ---

def test_IT_bounces_resolves_to_inanimate():
    """Both bindings enter the pipeline. Only INANIMATE_NP INANIMATE_VP
    reaches SENTENCE in Layer 3. Result: exactly 1 SENTENCE."""
    ls = make_scanner()
    result = ls.scan(['IT', 'bounces'], ['SENTENCE'])
    assert len(result) == 1
    assert result[0].labels == ['SENTENCE']

def test_IT_throws_resolves_to_animate():
    """IT throws the ball — INANIMATE binding eliminated, ANIMATE binding survives.
    Returns multiple spans (SV + SVO both valid), all from the ANIMATE path."""
    ls = make_scanner()
    result = ls.scan(['IT', 'throws', 'the', 'ball'], ['SENTENCE'])
    # at least one result — ANIMATE binding survived
    assert len(result) >= 1
    # the full SVO span is among the results
    assert any('ANIMATE_NP ANIMATE_VP INANIMATE_NP' in m.text for m in result)
    # no result where IT took the INANIMATE binding (would start with INANIMATE_NP)
    assert not any(m.text.startswith('INANIMATE_NP') for m in result)

def test_IT_chases_animate_object():
    """IT chases bob — only ANIMATE binding survives."""
    ls = make_scanner()
    result = ls.scan(['IT', 'chases', 'bob'], ['SENTENCE'])
    assert len(result) >= 1
    assert any('ANIMATE_NP ANIMATE_VP ANIMATE_NP' in m.text for m in result)
    assert not any('INANIMATE_NP' in m.text for m in result)


# --- unambiguous sentences still work ---

def test_alice_reads():
    ls = make_scanner()
    result = ls.scan(['alice', 'reads'], ['SENTENCE'])
    assert len(result) == 1

def test_alice_throws_the_ball():
    """Both SV ('alice throws') and SVO ('alice throws the ball') are valid spans."""
    ls = make_scanner()
    result = ls.scan(['alice', 'throws', 'the', 'ball'], ['SENTENCE'])
    assert len(result) >= 1
    assert any('ANIMATE_NP ANIMATE_VP INANIMATE_NP' in m.text for m in result)

def test_the_ball_bounces():
    ls = make_scanner()
    result = ls.scan(['the', 'ball', 'bounces'], ['SENTENCE'])
    assert len(result) == 1

def test_alice_chases_bob():
    ls = make_scanner()
    result = ls.scan(['alice', 'chases', 'bob'], ['SENTENCE'])
    assert len(result) >= 1
    assert any('ANIMATE_NP ANIMATE_VP ANIMATE_NP' in m.text for m in result)


# --- incoherent sentences produce no result ---

def test_alice_bounces_is_incoherent():
    """Animate subject with inanimate verb — eliminated at Layer 3."""
    ls = make_scanner()
    result = ls.scan(['alice', 'bounces'], ['SENTENCE'])
    assert result == []

def test_ball_throws_is_incoherent():
    """Inanimate subject with animate verb — eliminated at Layer 3."""
    ls = make_scanner()
    result = ls.scan(['the', 'ball', 'throws'], ['SENTENCE'])
    assert result == []
