"""
Forward chaining over a logic grid puzzle.

The key test: given only the 3 base clues, does the forward chainer
automatically derive the complete solution without any manual guidance?

Puzzle:
    People: alice, bob, carol
    Pets:   cat, dog, fish
    Drinks: tea, coffee, milk

Base clues (given):
    alice=cat, bob=coffee, dog=milk (rule: dog owner drinks milk)

Complete solution:
    alice : cat  / tea
    bob   : fish / coffee
    carol : dog  / milk

The reasoner is trained on deduction chains. forward_chain() iteratively
queries all ordered subsets of known facts, collects new predictions,
and repeats until stable — no manual deduction steps needed.
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, forward_chain


def make_reasoner():
    hdr = Hydraseq('logic')
    hdr.insert("alice=cat")
    hdr.insert("bob=coffee")
    hdr.insert("dog=milk")
    hdr.insert("alice=cat alice!=dog")
    hdr.insert("bob=coffee bob!=milk")
    hdr.insert("bob!=milk dog=milk bob!=dog")
    hdr.insert("alice!=dog bob!=dog carol=dog")
    hdr.insert("carol=dog dog=milk carol=milk")
    hdr.insert("bob=coffee carol=milk alice=tea")
    hdr.insert("alice=cat carol=dog bob=fish")
    return hdr


BASE_CLUES = {'alice=cat', 'bob=coffee', 'dog=milk'}

SOLUTION = {
    'alice=cat',   'alice=tea',
    'bob=coffee',  'bob=fish',
    'carol=dog',   'carol=milk',
}

DERIVED = {
    'alice!=dog',
    'bob!=milk',
    'bob!=dog',
    'carol=dog',
    'carol=milk',
    'alice=tea',
    'bob=fish',
}


# --- forward chainer derives the full solution ---

def test_derives_complete_solution():
    """Starting from 3 base clues, all solution facts are automatically derived."""
    hdr = make_reasoner()
    known, _ = forward_chain(hdr, BASE_CLUES)
    assert SOLUTION.issubset(known), f"Missing: {SOLUTION - known}"

def test_derives_all_intermediate_facts():
    """All intermediate deduction steps are also derived."""
    hdr = make_reasoner()
    known, _ = forward_chain(hdr, BASE_CLUES)
    assert DERIVED.issubset(known), f"Missing: {DERIVED - known}"

def test_no_wrong_facts_derived():
    """No incorrect facts appear in the derived set."""
    hdr = make_reasoner()
    known, _ = forward_chain(hdr, BASE_CLUES)
    wrong_facts = {
        'alice=dog', 'alice=fish',
        'alice=coffee', 'alice=milk',
        'bob=cat', 'bob=dog',
        'bob=tea', 'bob=milk',
        'carol=cat', 'carol=fish',
        'carol=tea', 'carol=coffee',
    }
    found_wrong = wrong_facts & known
    assert not found_wrong, f"Wrong facts derived: {found_wrong}"

def test_converges_quickly():
    """The chainer should stabilise in a small number of iterations."""
    hdr = make_reasoner()
    _, iterations = forward_chain(hdr, BASE_CLUES)
    assert iterations <= 5, f"Took {iterations} iterations — unexpectedly slow"

def test_base_facts_preserved():
    """Base clues remain in the derived set."""
    hdr = make_reasoner()
    known, _ = forward_chain(hdr, BASE_CLUES)
    assert BASE_CLUES.issubset(known)


# --- chainer is stable once complete ---

def test_idempotent_from_full_solution():
    """Running the chainer on the complete solution produces no new facts."""
    hdr = make_reasoner()
    full = BASE_CLUES | DERIVED
    known, iterations = forward_chain(hdr, full)
    assert iterations == 0, "Should need zero iterations when already complete"

def test_partial_clues_derive_partial_solution():
    """With only one base clue, only directly reachable facts are derived."""
    hdr = make_reasoner()
    known, _ = forward_chain(hdr, {'alice=cat'})
    # alice=cat directly implies alice!=dog
    assert 'alice!=dog' in known
    # bob's assignments require bob=coffee as a clue — shouldn't appear
    assert 'bob!=milk' not in known
    assert 'alice=tea' not in known
