"""
Experiment: can Hydraseq solve a simple logic grid puzzle by chaining deductions?

Puzzle:
    People: alice, bob, carol
    Pets:   cat, dog, fish
    Drinks: tea, coffee, milk

Clues:
    1. alice has the cat
    2. bob drinks coffee
    3. the dog owner drinks milk

Solution:
    alice : cat  / tea
    bob   : fish / coffee
    carol : dog  / milk

Each deduction step is encoded as a sequence where the final token is the conclusion.
We train the trie on these chains, then feed it the base clues and check whether it
predicts the derived facts correctly.
"""
import sys
sys.path.insert(0, '.')
from hydraseq import Hydraseq


def make_reasoner():
    hdr = Hydraseq('logic')

    # Base clues — single-token "sequences" so the trie knows these facts exist
    hdr.insert("alice=cat")
    hdr.insert("bob=coffee")
    hdr.insert("dog=milk")

    # Deduction chains: premise(s) followed by conclusion
    hdr.insert("alice=cat alice!=dog")
    hdr.insert("bob=coffee bob!=milk")
    hdr.insert("bob!=milk dog=milk bob!=dog")
    hdr.insert("alice!=dog bob!=dog carol=dog")
    hdr.insert("carol=dog dog=milk carol=milk")
    hdr.insert("bob=coffee carol=milk alice=tea")
    hdr.insert("alice=cat carol=dog bob=fish")

    return hdr


# --- base clues are recognized ---

def test_knows_alice_has_cat():
    hdr = make_reasoner()
    assert 'alice=cat' in hdr.look_ahead("alice=cat").get_active_values()

def test_knows_bob_drinks_coffee():
    hdr = make_reasoner()
    assert 'bob=coffee' in hdr.look_ahead("bob=coffee").get_active_values()

def test_knows_dog_milk_rule():
    hdr = make_reasoner()
    assert 'dog=milk' in hdr.look_ahead("dog=milk").get_active_values()


# --- single-step deductions ---

def test_alice_has_cat_implies_not_dog():
    hdr = make_reasoner()
    assert 'alice!=dog' in hdr.look_ahead("alice=cat").get_next_values()

def test_bob_drinks_coffee_implies_not_milk():
    hdr = make_reasoner()
    assert 'bob!=milk' in hdr.look_ahead("bob=coffee").get_next_values()

def test_bob_not_milk_plus_rule_implies_bob_not_dog():
    hdr = make_reasoner()
    assert 'bob!=dog' in hdr.look_ahead("bob!=milk dog=milk").get_next_values()


# --- multi-step deductions ---

def test_elimination_gives_carol_dog():
    hdr = make_reasoner()
    assert 'carol=dog' in hdr.look_ahead("alice!=dog bob!=dog").get_next_values()

def test_carol_dog_plus_rule_gives_carol_milk():
    hdr = make_reasoner()
    assert 'carol=milk' in hdr.look_ahead("carol=dog dog=milk").get_next_values()

def test_elimination_gives_alice_tea():
    hdr = make_reasoner()
    assert 'alice=tea' in hdr.look_ahead("bob=coffee carol=milk").get_next_values()

def test_elimination_gives_bob_fish():
    hdr = make_reasoner()
    assert 'bob=fish' in hdr.look_ahead("alice=cat carol=dog").get_next_values()


# --- chained: feed clues in sequence, check full solution is reachable ---

def test_chain_from_clues_to_carol_dog():
    """Starting from base clues, step through deductions to reach carol=dog."""
    hdr = make_reasoner()
    # alice=cat -> alice!=dog
    assert 'alice!=dog' in hdr.look_ahead("alice=cat").get_next_values()
    # bob=coffee -> bob!=milk
    assert 'bob!=milk' in hdr.look_ahead("bob=coffee").get_next_values()
    # bob!=milk + dog=milk -> bob!=dog
    assert 'bob!=dog' in hdr.look_ahead("bob!=milk dog=milk").get_next_values()
    # alice!=dog + bob!=dog -> carol=dog
    assert 'carol=dog' in hdr.look_ahead("alice!=dog bob!=dog").get_next_values()

def test_chain_from_carol_dog_to_full_solution():
    """From carol=dog, derive the remaining assignments."""
    hdr = make_reasoner()
    # carol=dog + dog=milk -> carol=milk
    assert 'carol=milk' in hdr.look_ahead("carol=dog dog=milk").get_next_values()
    # bob=coffee + carol=milk -> alice=tea
    assert 'alice=tea' in hdr.look_ahead("bob=coffee carol=milk").get_next_values()
    # alice=cat + carol=dog -> bob=fish
    assert 'bob=fish' in hdr.look_ahead("alice=cat carol=dog").get_next_values()
