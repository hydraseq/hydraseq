import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq
sys.path.append('./tests/data/')
import shapes as shapes
from automata import *

def test_convert_to_mermaid():
    transitions = [
        "s1 a ^s2",
        "s1 b ^s1",
        "s2 a ^s2",
        "s2 b ^s3",
        "s3 a ^s3",
        "s3 b ^s3"
    ]
    expected = '''s1((s1)) --a--> s2((s2))
s1((s1)) --b--> s1((s1))
s2((s2)) --a--> s2((s2))
s2((s2)) --b--> s3((s3))
s3((s3)) --a--> s3((s3))
s3((s3)) --b--> s3((s3))'''
    dfa = DFAstate(transitions, 's1')
    assert dfa.convert_to_mermaid() == expected

#
# Examples are from understanding compuation chapter 2
#
def test_two_state():
    """Simple toggle between two states"""
    transitions = [
        "s1 a ^s2",
        "s2 a ^s1"
    ]
    dfa = DFAstate(transitions, 's1')

    input_string = "aaaaaa"
    current_state = 's1'
    for letter in input_string:
        current_state = 's1' if current_state == 's2' else 's2'
        dfa.event(letter)
        assert current_state == dfa.get_active_states().pop()

def test_two_state_accept_odds():
    """Toggle between two states, but accepting only on s2.  Accepts odd length strings"""
    transitions = [
        "s1 a ^s2",
        "s2 a ^s1"
    ]
    dfa = DFAstate(transitions, 's1', accepting_states=['s2'])

    input_string = "aaaaaa"
    current_state = 's1'
    accepting = False
    for letter in input_string:
        current_state = 's1' if current_state == 's2' else 's2'
        accepting = False if accepting else True
        assert current_state == dfa.event(letter).get_active_states()[0]
        assert accepting == dfa.in_accepting()

def test_tri_state_automata():
    """Only accept strings that contain sequence ab. Pg 65"""
    transitions = [
        "s1 a ^s2",
        "s1 b ^s1",
        "s2 a ^s2",
        "s2 b ^s3",
        "s3 a ^s3",
        "s3 b ^s3"
    ]
    dfa = DFAstate(transitions, 's1', accepting_states=['s3'])
    print(dfa.convert_to_mermaid())

    accepts = [
        "abaa",
        "aaaaaba",
        "aaaaaaab"
    ]
    rejects = [
        "aaaaa",
        "aaaaaaa",
        "baaaa"
    ]
    for accept in accepts:
        assert dfa.read_string(accept).in_accepting() == True, accept + " should be accepted"
    for reject in rejects:
        assert dfa.read_string(reject).in_accepting() == False, reject+" should be rejected"

def test_deterministic_b_is_third_from_start_70():
    """Accept any length string as long as third character is a b"""
    transitions = [
        "s1 a,b ^s2",
        "s2 a,b ^s3",
        "s3 a ^s4",
        "s3 b ^s5",
        "s4 a,b ^s4",
        "s5 a,b ^s5"
    ]

    dfa = DFAstate(transitions, 's1', accepting_states=['s5'])
    print(dfa.convert_to_mermaid())

    accepts = [
        "aabaa",
        "aabaaba",
        "aabaaaab"
    ]
    rejects = [
        "aaaaa",
        "aaaaaaa",
        "baaaa"
    ]
    for accept in accepts:
        assert dfa.read_string(accept).in_accepting() == True, accept + " should be accepted"
    for reject in rejects:
        assert dfa.read_string(reject).in_accepting() == False, reject+" should be rejected"

def test_non_deterministic_b_is_third_from_last_70():
    """Accept any length string as long as third character is a b"""
    transitions = [
        "s1 a,b ^s1",
        "s1 b ^s2",
        "s2 a,b ^s3",
        "s3 a,b ^s4",
        "s4"
    ]

    dfa = DFAstate(transitions, 's1', accepting_states=['s4'])
    print(dfa.convert_to_mermaid())

    accepts = [
        "aaabaa",
        "aaaabba",
        "aaaaabab"
    ]
    rejects = [
        "aaaaa",
        "aaaaaaa",
        "baaaa"
    ]
    for accept in accepts:
        assert dfa.read_string(accept).in_accepting() == True, accept + " should be accepted"
    for reject in rejects:
        assert dfa.read_string(reject).in_accepting() == False, reject+" should be rejected"

def test_non_deterministic_multiples_two_and_three_76():
    """Accept strings that are multiples of 2 or 3 in length"""
    transitions = [
        "s1 a ^s2",
        "s2 a ^s1",
        "s1 a ^s3",
        "s3 a ^s4",
        "s4 a ^s1"
    ]

    dfa = DFAstate(transitions, 's1', accepting_states=['s1'])
    print(dfa.convert_to_mermaid())

    accepts = [
        2*"a",
        3*"a",
        4*"a",
        5*"a",
        6*"a",
        7*"a",
        8*"a"
    ]
    rejects = [
    ]
    for accept in accepts:
        assert dfa.read_string(accept).in_accepting() == True, accept + " should be accepted"
    for reject in rejects:
        assert dfa.read_string(reject).in_accepting() == False, reject+" should be rejected"

def test_non_deterministic_with_free_moves_78():
    """Accept strings that are multiples of 2 or 3 in length"""
    transitions = [
        "s1 n ^s2",
        "s1 n ^s4",
        "s2 a ^s3",
        "s3 a ^s2",
        "s4 a ^s5",
        "s5 a ^s6",
        "s6 a ^s4"
    ]

    dfa = DFAstate(transitions, 's1', accepting_states=['s2','s4'])
    print(dfa.convert_to_mermaid())

    # use n to mean a free move, triggers both states 2 and 4 from the get go simultaneous
    accepts = [ # accepts multiples of 2 or 3, 2,3,4,6,8 etc..
        "naa",
        "naaa",
        "naaaa",
        "naaaaaa",
        "naaaaaaaa"
    ]
    rejects = [ # should reject non-multiples of 2,3, such as 5, 7 etc
        "naaaaa",
        "naaaaaaa",
    ]
    for accept in accepts:
        assert dfa.read_string(accept).in_accepting() == True, accept + " should be accepted"
    for reject in rejects:
        assert dfa.read_string(reject).in_accepting() == False, reject+" should be rejected"
