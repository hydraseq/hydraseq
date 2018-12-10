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
    assert convert_to_mermaid(transitions) == expected


def test_two_state():
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

def test_tri_state_automata():

    transitions = [
        "s1 a ^s2",
        "s1 b ^s1",
        "s2 a ^s2",
        "s2 b ^s3",
        "s3 a ^s3",
        "s3 b ^s3"
    ]
    dfa = DFAstate(transitions, 's1')
    print(dfa)
    for letter in "bbabba":
        print(letter, dfa.event(letter))
