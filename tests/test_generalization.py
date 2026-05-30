"""
Level 1 generalization test: same logical structure, completely new vocabulary.

Original puzzle: alice/bob/carol, cat/dog/fish, tea/coffee/milk
New puzzle:      xavier/yvonne/zara, parrot/snake/turtle, juice/soda/water

Structure is identical:
    Clue 1: person1 has pet1          (xavier=parrot)
    Clue 2: person2 drinks drink2     (yvonne=soda)
    Clue 3: pet2 owner drinks drink3  (snake=water)

    Solution:
        xavier : parrot / juice
        yvonne : turtle / soda
        zara   : snake  / water

Three things verified here:
    1. A new reasoner with the same structural rules solves the new puzzle
       → the APPROACH generalizes
    2. The original reasoner (alice vocab) cannot solve the new puzzle
       → the solution isn't hiding in memorized tokens
    3. Deduction chains can be generated from a puzzle spec programmatically
       → bridge toward Level 2 (variable binding)
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, forward_chain


# ── original puzzle (for comparison) ──────────────────────────────────────────

def make_original_reasoner():
    hdr = Hydraseq('original')
    hdr.insert("alice=cat");  hdr.insert("bob=coffee");  hdr.insert("dog=milk")
    hdr.insert("alice=cat alice!=dog")
    hdr.insert("bob=coffee bob!=milk")
    hdr.insert("bob!=milk dog=milk bob!=dog")
    hdr.insert("alice!=dog bob!=dog carol=dog")
    hdr.insert("carol=dog dog=milk carol=milk")
    hdr.insert("bob=coffee carol=milk alice=tea")
    hdr.insert("alice=cat carol=dog bob=fish")
    return hdr

ORIGINAL_BASE     = {'alice=cat', 'bob=coffee', 'dog=milk'}
ORIGINAL_SOLUTION = {'alice=cat', 'alice=tea', 'bob=coffee', 'bob=fish',
                     'carol=dog', 'carol=milk'}


# ── new puzzle ─────────────────────────────────────────────────────────────────

def make_chains(p1, p2, p3, pet1, pet2, pet3, d1, d2, d3):
    """Generate deduction chains for a 3x3 logic puzzle of this structure:
        clue1: p1 = pet1
        clue2: p2 = d2
        clue3: pet2 owner drinks d3
    Returns list of sequence strings to insert into a Hydraseq.
    """
    return [
        # base clues
        f"{p1}={pet1}",
        f"{p2}={d2}",
        f"{pet2}={d3}",
        # single-step deductions
        f"{p1}={pet1} {p1}!={pet2}",
        f"{p2}={d2} {p2}!={d3}",
        # two-step deductions
        f"{p2}!={d3} {pet2}={d3} {p2}!={pet2}",
        f"{p1}!={pet2} {p2}!={pet2} {p3}={pet2}",
        f"{p3}={pet2} {pet2}={d3} {p3}={d3}",
        f"{p2}={d2} {p3}={d3} {p1}={d1}",
        f"{p1}={pet1} {p3}={pet2} {p2}={pet3}",
    ]


def make_new_reasoner():
    """Same logical structure as original, completely new vocabulary."""
    hdr = Hydraseq('new')
    for chain in make_chains(
        p1='xavier', p2='yvonne', p3='zara',
        pet1='parrot', pet2='snake', pet3='turtle',
        d1='juice', d2='soda', d3='water'
    ):
        hdr.insert(chain)
    return hdr


NEW_BASE     = {'xavier=parrot', 'yvonne=soda', 'snake=water'}
NEW_SOLUTION = {'xavier=parrot', 'xavier=juice',
                'yvonne=soda',   'yvonne=turtle',
                'zara=snake',    'zara=water'}
NEW_WRONG    = {'xavier=snake', 'xavier=turtle',
                'yvonne=parrot', 'yvonne=snake',
                'zara=parrot',   'zara=turtle'}


# ── 1. new reasoner solves new puzzle ─────────────────────────────────────────

def test_new_puzzle_derives_complete_solution():
    hdr = make_new_reasoner()
    known, _ = forward_chain(hdr, NEW_BASE)
    assert NEW_SOLUTION.issubset(known), f"Missing: {NEW_SOLUTION - known}"

def test_new_puzzle_no_wrong_facts():
    hdr = make_new_reasoner()
    known, _ = forward_chain(hdr, NEW_BASE)
    assert not (NEW_WRONG & known), f"Wrong facts: {NEW_WRONG & known}"

def test_new_puzzle_converges_quickly():
    hdr = make_new_reasoner()
    _, iterations = forward_chain(hdr, NEW_BASE)
    assert iterations <= 5


# ── 2. original reasoner cannot solve new puzzle ──────────────────────────────

def test_original_reasoner_fails_on_new_vocab():
    """The original reasoner knows nothing about xavier/parrot/soda.
    This confirms the new puzzle solution isn't hiding in memorized tokens."""
    hdr = make_original_reasoner()
    known, _ = forward_chain(hdr, NEW_BASE)
    # should derive nothing beyond the base clues themselves
    derived = known - NEW_BASE
    assert not derived, f"Original reasoner unexpectedly derived: {derived}"

def test_new_reasoner_fails_on_original_vocab():
    """Symmetric check: new reasoner knows nothing about alice/cat/coffee."""
    hdr = make_new_reasoner()
    known, _ = forward_chain(hdr, ORIGINAL_BASE)
    derived = known - ORIGINAL_BASE
    assert not derived, f"New reasoner unexpectedly derived: {derived}"


# ── 3. make_chains generates valid reasoning for original puzzle too ───────────

def test_make_chains_works_for_original_puzzle():
    """The chain generator produces correct deductions for the original vocab."""
    hdr = Hydraseq('generated')
    for chain in make_chains(
        p1='alice', p2='bob', p3='carol',
        pet1='cat', pet2='dog', pet3='fish',
        d1='tea', d2='coffee', d3='milk'
    ):
        hdr.insert(chain)

    known, _ = forward_chain(hdr, ORIGINAL_BASE)
    assert ORIGINAL_SOLUTION.issubset(known), f"Missing: {ORIGINAL_SOLUTION - known}"

def test_make_chains_solves_third_puzzle():
    """A third puzzle with yet another vocabulary, generated programmatically."""
    hdr = Hydraseq('third')
    for chain in make_chains(
        p1='red', p2='blue', p3='green',
        pet1='circle', pet2='square', pet3='triangle',
        d1='hot', d2='cold', d3='warm'
    ):
        hdr.insert(chain)

    base     = {'red=circle', 'blue=cold', 'square=warm'}
    solution = {'red=circle', 'red=hot',
                'blue=cold',  'blue=triangle',
                'green=square', 'green=warm'}

    known, _ = forward_chain(hdr, base)
    assert solution.issubset(known), f"Missing: {solution - known}"
