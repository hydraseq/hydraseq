"""
Experiment: pronoun resolution via sequence disambiguation.

Sentence: "the book didn't fit in my bag because IT was too small"

IT is ambiguous — it could refer to 'book' (OBJECT) or 'bag' (CONTAINER).
Only one binding produces a coherent causal sequence given the sentence context.

Key parallel to addrext: just as 'st' encodes as both SAINT and STREET simultaneously,
IT encodes as both OBJECT and CONTAINER simultaneously. The surrounding sequence
context eliminates the incoherent binding.

Rules taught as sequences:
    CONTAINER too_small -> not_fit   (container too small: contents don't fit)
    OBJECT    too_small -> fits      (object too small: it fits fine)

The sentence tells us the outcome is 'not_fit'.
Only IT=CONTAINER (bag) leads to that prediction — IT=OBJECT (book) predicts 'fits',
contradicting the sentence.
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, PatternScanner


def encoder(token):
    """Map raw tokens to semantic category labels.
    IT is intentionally ambiguous: both OBJECT and CONTAINER.
    """
    mapping = {
        'book':      ['OBJECT'],
        'bag':       ['CONTAINER'],
        'IT':        ['OBJECT', 'CONTAINER'],   # ambiguous pronoun
        'too_small': ['SIZE_CONSTRAINT'],
        'not_fit':   ['NEGATIVE_FIT'],
        'fits':      ['POSITIVE_FIT'],
    }
    return mapping.get(token, ['UNKNOWN'])


def make_reasoner():
    hdr = Hydraseq('pronoun')
    # Physical causal rules as category sequences
    hdr.insert([['CONTAINER'], ['SIZE_CONSTRAINT'], ['NEGATIVE_FIT']])
    hdr.insert([['OBJECT'],    ['SIZE_CONSTRAINT'], ['POSITIVE_FIT']])
    return hdr


# --- encoder sanity checks ---

def test_book_encodes_as_object():
    assert encoder('book') == ['OBJECT']

def test_bag_encodes_as_container():
    assert encoder('bag') == ['CONTAINER']

def test_IT_encodes_as_both():
    cats = encoder('IT')
    assert 'OBJECT' in cats
    assert 'CONTAINER' in cats


# --- rules are learned ---

def test_container_too_small_predicts_not_fit():
    hdr = make_reasoner()
    result = hdr.look_ahead([['CONTAINER'], ['SIZE_CONSTRAINT']]).get_next_values()
    assert 'NEGATIVE_FIT' in result

def test_object_too_small_predicts_fits():
    hdr = make_reasoner()
    result = hdr.look_ahead([['OBJECT'], ['SIZE_CONSTRAINT']]).get_next_values()
    assert 'POSITIVE_FIT' in result


# --- ambiguity: IT holds both predictions simultaneously ---

def test_IT_too_small_predicts_both_outcomes():
    """When IT is ambiguous, the trie predicts both possible outcomes —
    this is the moment of held ambiguity, analogous to 'st' in addrext."""
    hdr = make_reasoner()
    result = hdr.look_ahead([encoder('IT'), ['SIZE_CONSTRAINT']]).get_next_values()
    assert 'NEGATIVE_FIT' in result, "CONTAINER binding should predict not_fit"
    assert 'POSITIVE_FIT' in result, "OBJECT binding should predict fits"


# --- resolution: sentence context selects the correct binding ---

def test_not_fit_context_selects_container_binding():
    """The sentence says 'didn't fit' (NEGATIVE_FIT).
    Only IT=CONTAINER leads to that prediction.
    Therefore IT must refer to bag, not book."""
    hdr = make_reasoner()
    predictions = hdr.look_ahead([encoder('IT'), ['SIZE_CONSTRAINT']]).get_next_values()

    # sentence outcome is not_fit — filter predictions to match context
    sentence_outcome = 'NEGATIVE_FIT'
    assert sentence_outcome in predictions

    # now find which binding of IT produced that outcome
    resolved = []
    for candidate, label in [('book', 'OBJECT'), ('bag', 'CONTAINER')]:
        result = hdr.look_ahead([[label], ['SIZE_CONSTRAINT']]).get_next_values()
        if sentence_outcome in result:
            resolved.append(candidate)

    assert resolved == ['bag'], "Only 'bag' (CONTAINER) produces NEGATIVE_FIT"

def test_fits_context_would_select_object_binding():
    """Sanity check: if the sentence had said 'it fits', IT would resolve to book."""
    hdr = make_reasoner()
    sentence_outcome = 'POSITIVE_FIT'

    resolved = []
    for candidate, label in [('book', 'OBJECT'), ('bag', 'CONTAINER')]:
        result = hdr.look_ahead([[label], ['SIZE_CONSTRAINT']]).get_next_values()
        if sentence_outcome in result:
            resolved.append(candidate)

    assert resolved == ['book'], "Only 'book' (OBJECT) produces POSITIVE_FIT"


# --- using PatternScanner to find the coherent span ---

def test_scanner_finds_coherent_binding():
    """PatternScanner slides over the token stream.
    The span [IT, too_small] should resolve to NEGATIVE_FIT (via CONTAINER binding)
    and not to POSITIVE_FIT, given the sentence context."""
    hdr = make_reasoner()
    scanner = PatternScanner(hdr, encoder)

    # the relevant fragment of the sentence
    tokens = ['IT', 'too_small']

    neg_markers = scanner.get_markers(tokens, ['NEGATIVE_FIT'])
    pos_markers = scanner.get_markers(tokens, ['POSITIVE_FIT'])

    # both are found — ambiguity is held
    assert len(neg_markers) > 0
    assert len(pos_markers) > 0

    # but the sentence context (not_fit) selects NEGATIVE_FIT -> CONTAINER -> bag
    assert neg_markers[0].text == 'IT too_small'
    assert pos_markers[0].text == 'IT too_small'

    # resolution: pick the marker whose label matches the sentence outcome
    sentence_outcome = 'NEGATIVE_FIT'
    resolved_markers = [m for m in neg_markers if sentence_outcome in m.labels]
    assert len(resolved_markers) == 1
