"""
Level 2 generalization: one abstract reasoner solves any puzzle with the same structure.

The abstract reasoner is trained ONCE on role-level deduction rules:
    PERSON1=PET1, PERSON2=DRINK2, PET2=DRINK3  (base clue patterns)
    PERSON1=PET1 -> PERSON1!=PET2               (exclusivity)
    PERSON2=DRINK2 -> PERSON2!=DRINK3           (exclusivity)
    PERSON2!=DRINK3 + PET2=DRINK3 -> PERSON2!=PET2
    PERSON1!=PET2 + PERSON2!=PET2 -> PERSON3=PET2   (elimination)
    PERSON3=PET2 + PET2=DRINK3 -> PERSON3=DRINK3
    PERSON2=DRINK2 + PERSON3=DRINK3 -> PERSON1=DRINK1
    PERSON1=PET1 + PERSON3=PET2 -> PERSON2=PET3

A RoleMapper translates between specific tokens and abstract roles.
solve_puzzle() encodes clues to roles, runs forward_chain, decodes back.

Three different puzzles, same abstract reasoner:
    Puzzle 1: alice/bob/carol,   cat/dog/fish,         tea/coffee/milk
    Puzzle 2: xavier/yvonne/zara, parrot/snake/turtle,  juice/soda/water
    Puzzle 3: red/blue/green,    circle/square/triangle, hot/cold/warm
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq, RoleMapper, solve_puzzle


def make_abstract_reasoner():
    """Trained once on abstract role-level rules. Solves any structurally
    identical puzzle — specific token names are never seen by this reasoner."""
    hdr = Hydraseq('abstract')

    # base clue patterns (so the trie recognises them as starting points)
    hdr.insert("PERSON1=PET1")
    hdr.insert("PERSON2=DRINK2")
    hdr.insert("PET2=DRINK3")

    # abstract deduction rules
    hdr.insert("PERSON1=PET1 PERSON1!=PET2")
    hdr.insert("PERSON2=DRINK2 PERSON2!=DRINK3")
    hdr.insert("PERSON2!=DRINK3 PET2=DRINK3 PERSON2!=PET2")
    hdr.insert("PERSON1!=PET2 PERSON2!=PET2 PERSON3=PET2")
    hdr.insert("PERSON3=PET2 PET2=DRINK3 PERSON3=DRINK3")
    hdr.insert("PERSON2=DRINK2 PERSON3=DRINK3 PERSON1=DRINK1")
    hdr.insert("PERSON1=PET1 PERSON3=PET2 PERSON2=PET3")

    return hdr


# one reasoner for all three puzzles
ABSTRACT = make_abstract_reasoner()

PUZZLE_1 = dict(
    role_map={
        'alice': 'PERSON1', 'bob': 'PERSON2',  'carol': 'PERSON3',
        'cat':   'PET1',    'dog': 'PET2',     'fish':  'PET3',
        'tea':   'DRINK1',  'coffee': 'DRINK2', 'milk': 'DRINK3',
    },
    base    = {'alice=cat', 'bob=coffee', 'dog=milk'},
    solution= {'alice=cat', 'alice=tea',
               'bob=coffee', 'bob=fish',
               'carol=dog',  'carol=milk'},
    wrong   = {'alice=dog', 'alice=fish', 'bob=cat', 'bob=dog',
               'carol=cat', 'carol=fish'},
)

PUZZLE_2 = dict(
    role_map={
        'xavier': 'PERSON1', 'yvonne': 'PERSON2', 'zara':   'PERSON3',
        'parrot': 'PET1',    'snake':  'PET2',    'turtle': 'PET3',
        'juice':  'DRINK1',  'soda':   'DRINK2',  'water':  'DRINK3',
    },
    base    = {'xavier=parrot', 'yvonne=soda', 'snake=water'},
    solution= {'xavier=parrot', 'xavier=juice',
               'yvonne=soda',   'yvonne=turtle',
               'zara=snake',    'zara=water'},
    wrong   = {'xavier=snake', 'xavier=turtle', 'yvonne=parrot', 'yvonne=snake',
               'zara=parrot',  'zara=turtle'},
)

PUZZLE_3 = dict(
    role_map={
        'red':    'PERSON1', 'blue':   'PERSON2', 'green':    'PERSON3',
        'circle': 'PET1',    'square': 'PET2',    'triangle': 'PET3',
        'hot':    'DRINK1',  'cold':   'DRINK2',  'warm':     'DRINK3',
    },
    base    = {'red=circle', 'blue=cold', 'square=warm'},
    solution= {'red=circle',   'red=hot',
               'blue=cold',    'blue=triangle',
               'green=square', 'green=warm'},
    wrong   = {'red=square', 'red=triangle', 'blue=circle', 'blue=square',
               'green=circle', 'green=triangle'},
)


# ── RoleMapper ────────────────────────────────────────────────────────────────

def test_role_mapper_encodes_fact():
    m = RoleMapper(PUZZLE_1['role_map'])
    assert m.encode('alice=cat')  == 'PERSON1=PET1'
    assert m.encode('bob=coffee') == 'PERSON2=DRINK2'
    assert m.encode('dog=milk')   == 'PET2=DRINK3'

def test_role_mapper_encodes_negation():
    m = RoleMapper(PUZZLE_1['role_map'])
    assert m.encode('alice!=dog') == 'PERSON1!=PET2'
    assert m.encode('bob!=milk')  == 'PERSON2!=DRINK3'

def test_role_mapper_decodes_fact():
    m = RoleMapper(PUZZLE_1['role_map'])
    assert m.decode('PERSON3=PET2')   == 'carol=dog'
    assert m.decode('PERSON1=DRINK1') == 'alice=tea'
    assert m.decode('PERSON2=PET3')   == 'bob=fish'

def test_role_mapper_roundtrip():
    m = RoleMapper(PUZZLE_1['role_map'])
    for fact in ['alice=cat', 'bob!=milk', 'carol=dog']:
        assert m.decode(m.encode(fact)) == fact


# ── abstract reasoner derives correct role-level solution ─────────────────────

def test_abstract_reasoner_derives_role_solution():
    from hydraseq import forward_chain
    abstract_base = {'PERSON1=PET1', 'PERSON2=DRINK2', 'PET2=DRINK3'}
    known, _ = forward_chain(ABSTRACT, abstract_base)
    expected = {
        'PERSON1=PET1',    'PERSON1=DRINK1',
        'PERSON2=DRINK2',  'PERSON2=PET3',
        'PERSON3=PET2',    'PERSON3=DRINK3',
    }
    assert expected.issubset(known), f"Missing: {expected - known}"


# ── solve_puzzle: one abstract reasoner, three puzzles ────────────────────────

def test_puzzle_1_alice():
    p = PUZZLE_1
    solution = solve_puzzle(ABSTRACT, p['role_map'], p['base'])
    assert p['solution'].issubset(solution), f"Missing: {p['solution'] - solution}"
    assert not (p['wrong'] & solution), f"Wrong facts: {p['wrong'] & solution}"

def test_puzzle_2_xavier():
    p = PUZZLE_2
    solution = solve_puzzle(ABSTRACT, p['role_map'], p['base'])
    assert p['solution'].issubset(solution), f"Missing: {p['solution'] - solution}"
    assert not (p['wrong'] & solution), f"Wrong facts: {p['wrong'] & solution}"

def test_puzzle_3_colours():
    p = PUZZLE_3
    solution = solve_puzzle(ABSTRACT, p['role_map'], p['base'])
    assert p['solution'].issubset(solution), f"Missing: {p['solution'] - solution}"
    assert not (p['wrong'] & solution), f"Wrong facts: {p['wrong'] & solution}"

def test_same_reasoner_instance_used_for_all():
    """Explicitly verify the abstract reasoner is not retrained between puzzles.
    One object, three solve_puzzle calls, all correct."""
    reasoner = make_abstract_reasoner()
    for p in [PUZZLE_1, PUZZLE_2, PUZZLE_3]:
        solution = solve_puzzle(reasoner, p['role_map'], p['base'])
        assert p['solution'].issubset(solution)
