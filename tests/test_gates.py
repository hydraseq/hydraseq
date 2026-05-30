import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq


def make_and_gate():
    hdr = Hydraseq('and')
    hdr.insert("a b 1")
    hdr.insert("b a 1")
    return hdr


def make_or_gate():
    hdr = Hydraseq('or')
    hdr.insert("a 1")
    hdr.insert("b 1")
    hdr.insert("a b 1")
    hdr.insert("b a 1")
    return hdr


def make_xor_gate():
    hdr = Hydraseq('xor')
    hdr.insert("a 1")
    hdr.insert("b 1")
    hdr.insert("a b 0")
    hdr.insert("b a 0")
    return hdr


# AND gate

def test_and_both_inputs_a_then_b():
    hdr = make_and_gate()
    assert hdr.look_ahead("a b").get_next_values() == ['1']

def test_and_both_inputs_b_then_a():
    hdr = make_and_gate()
    assert hdr.look_ahead("b a").get_next_values() == ['1']

def test_and_single_input_a_predicts_b_not_output():
    # AND with only one input should not yet predict an output
    hdr = make_and_gate()
    nexts = hdr.look_ahead("a").get_next_values()
    assert '1' not in nexts
    assert 'b' in nexts

def test_and_single_input_b_predicts_a_not_output():
    hdr = make_and_gate()
    nexts = hdr.look_ahead("b").get_next_values()
    assert '1' not in nexts
    assert 'a' in nexts


# OR gate

def test_or_single_input_a():
    # OR with one input predicts '1' (can output now) and also 'b' (could wait for second input)
    hdr = make_or_gate()
    assert '1' in hdr.look_ahead("a").get_next_values()

def test_or_single_input_b():
    hdr = make_or_gate()
    assert '1' in hdr.look_ahead("b").get_next_values()

def test_or_both_inputs_a_then_b():
    hdr = make_or_gate()
    assert hdr.look_ahead("a b").get_next_values() == ['1']

def test_or_both_inputs_b_then_a():
    hdr = make_or_gate()
    assert hdr.look_ahead("b a").get_next_values() == ['1']


def make_nand_gate():
    hdr = Hydraseq('nand')
    hdr.insert("a b 0")
    hdr.insert("b a 0")
    hdr.insert("a 1")
    hdr.insert("b 1")
    return hdr


# NAND gate (universal — functionally complete on its own)

def test_nand_both_inputs_a_then_b():
    hdr = make_nand_gate()
    assert hdr.look_ahead("a b").get_next_values() == ['0']

def test_nand_both_inputs_b_then_a():
    hdr = make_nand_gate()
    assert hdr.look_ahead("b a").get_next_values() == ['0']

def test_nand_single_input_a():
    hdr = make_nand_gate()
    assert '1' in hdr.look_ahead("a").get_next_values()

def test_nand_single_input_b():
    hdr = make_nand_gate()
    assert '1' in hdr.look_ahead("b").get_next_values()


# XOR gate

def test_xor_single_input_a():
    hdr = make_xor_gate()
    assert '1' in hdr.look_ahead("a").get_next_values()

def test_xor_single_input_b():
    hdr = make_xor_gate()
    assert '1' in hdr.look_ahead("b").get_next_values()

def test_xor_both_inputs_a_then_b():
    hdr = make_xor_gate()
    assert hdr.look_ahead("a b").get_next_values() == ['0']

def test_xor_both_inputs_b_then_a():
    hdr = make_xor_gate()
    assert hdr.look_ahead("b a").get_next_values() == ['0']
