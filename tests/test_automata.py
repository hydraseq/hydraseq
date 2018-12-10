import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq
from hydraseq import *
from columns import *
sys.path.append('./tests/data/')
import shapes as shapes
from automata import *
import pytest

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
        assert current_state == dfa.event(letter).get_active_states()[0]

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