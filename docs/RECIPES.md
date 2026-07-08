# Hydraseq Recipes

Meaningful combinations of the atomic calls — each one is a working pattern proven by a
test file. For the atomic calls themselves see [API.md](API.md).

Every snippet below runs as shown; outputs are real.

| Recipe | Test that proves it |
|---|---|
| [1. Next-token prediction](#1-next-token-prediction) | [test_hydraseq.py](../tests/test_hydraseq.py) |
| [2. Streaming, one token at a time](#2-streaming-one-token-at-a-time) | [test_hydraseq.py](../tests/test_hydraseq.py) |
| [3. Novelty detection with surprise](#3-novelty-detection-with-surprise) | [test_hydraseq.py](../tests/test_hydraseq.py) |
| [4. Autocomplete](#4-autocomplete) | [test_autocomplete.py](../tests/test_autocomplete.py) |
| [5. Held ambiguity](#5-held-ambiguity) | [test_hydraseq.py](../tests/test_hydraseq.py) |
| [6. Logic gates](#6-logic-gates) | [test_gates.py](../tests/test_gates.py) |
| [7. Comparator (what changed?)](#7-comparator-what-changed) | [test_compare.py](../tests/test_compare.py) |
| [8. Span labeling with convolutions](#8-span-labeling-with-convolutions) | [test_hydraseq.py](../tests/test_hydraseq.py) |
| [9. Pattern scanning](#9-pattern-scanning) | [test_scanner.py](../tests/test_scanner.py) |
| [10. Layered scanning](#10-layered-scanning) | [test_layered_scanner.py](../tests/test_layered_scanner.py) |
| [11. Closed-loop semantic resolution](#11-closed-loop-semantic-resolution) | [test_closed_loop.py](../tests/test_closed_loop.py) |
| [12. Deduction by forward chaining](#12-deduction-by-forward-chaining) | [test_forward_chain.py](../tests/test_forward_chain.py) |
| [13. Variables via role mapping](#13-variables-via-role-mapping) | [test_abstract_reasoning.py](../tests/test_abstract_reasoning.py) |
| [14. Inference by analogy](#14-inference-by-analogy) | [test_cortical_experiment.py](../tests/test_cortical_experiment.py) |
| [15. State machines](#15-state-machines) | [test_automata.py](../tests/test_automata.py) |
| [16. World knowledge + Winograd schemas](#16-world-knowledge--winograd-schemas) | [test_winograd_resolver.py](../tests/test_winograd_resolver.py) |
| [17. Attention / top-down gating](#17-attention--top-down-gating) | [test_hydraseq.py](../tests/test_hydraseq.py) |

---

## 1. Next-token prediction

**The core loop: train on sequences, ask what comes next.** Branching prefixes return
every learned continuation.

```python
from hydraseq import Hydraseq

hdr = Hydraseq('main')
hdr.insert("the quick brown fox jumped over the lazy dog")
hdr.insert("the quick brown wolf jumped over the lazy dog")

hdr.look_ahead("the quick brown").get_next_values()
# ['fox', 'wolf']
```

**Use it for:** anything shaped like "given this prefix, what follows?" — command
prediction, log-line anticipation, melody continuation.

## 2. Streaming, one token at a time

`look_ahead` replays from the start every call. When input arrives incrementally,
`reset()` once and `hit()` each token as it comes — the cursor persists between calls.

```python
hdr.reset()
hdr.look_ahead("the").get_next_values()                  # ['quick']
hdr.hit(["quick"], is_learning=False).get_next_values()  # ['brown']
hdr.hit(["brown"], is_learning=False).get_next_values()  # ['fox', 'wolf']
```

**Use it for:** live streams — each event advances the cursor, predictions are always
current, and `surprise` fires the moment the stream leaves known territory.

## 3. Novelty detection with surprise

`surprise` flips to `True` whenever input departs from every known path. With
`insert` this means "I just learned something"; with `look_ahead` it means "this is
not in memory" — a yes/no familiarity test with no threshold to tune.

```python
h = Hydraseq('s')
h.insert("this is a test")
h.surprise                                # True  — it was new
h.insert("this is a test")
h.surprise                                # False — already known
h.look_ahead("what is this").surprise     # True  — unfamiliar, and NOT learned
```

**Use it for:** anomaly detection over event sequences; also the trigger for
delegating to another strategy (recipe 14 uses surprise to decide when analogy is
needed).

## 4. Autocomplete

Combine `look_ahead` (position at the prefix) with `forward_prediction()` (roll to all
reachable ends). Train character-by-character with an end marker.

```python
ac = Hydraseq('auto')
for name in ['efrain', 'efrom', 'efren', 'ephrem', 'efrainium']:
    ac.insert([[c] for c in name + '$'])

ac.look_ahead([[c] for c in 'efra'])
sorted(e.get_sequence().replace(' ', '')[:-1] for e in ac.forward_prediction())
# ['efrain', 'efrainium']
```

**Use it for:** completion over any token alphabet — names, file paths, API call
chains. The same two calls at word level answer "where could this sentence be going?"

## 5. Held ambiguity

A frame with multiple tokens means "either of these". The trie holds all consistent
interpretations at once; downstream context is what narrows them.

```python
hdr = Hydraseq('m')
hdr.insert([['a'], ['b'], ['d']])
hdr.insert([['a'], ['c'], ['d']])

r = hdr.look_ahead([['a'], ['b', 'c']])   # ambiguous second token
r.get_active_sequences()   # ['a b', 'a c']  — both alive
r.get_next_values()        # ['d']           — agreed prediction either way
```

**Use it for:** noisy or underdetermined input — OCR alternatives, homophones,
part-of-speech ambiguity. This is the primitive under recipes 9–11 and the addrext
'st' = SAINT-vs-STREET disambiguation.

## 6. Logic gates

Boolean gates are just short trained sequences: inputs in either order, capped with the
output. NAND is functionally complete, so learned sequences alone suffice for arbitrary
boolean computation.

```python
gate = Hydraseq('and')
gate.insert("a b 1")
gate.insert("b a 1")

gate.look_ahead("a b").get_next_values()   # ['1']
gate.look_ahead("a").get_next_values()     # ['b'] — no output yet, waiting for b
```

XOR needs the single-input cases too:

```python
xor = Hydraseq('xor')
for s in ["a 1", "b 1", "a b 0", "b a 0"]:
    xor.insert(s)
xor.look_ahead("a").get_next_values()      # ['1', 'b'] — 1 now, or b still pending
xor.look_ahead("a b").get_next_values()    # ['0']
```

Note the XOR single-input reading: the prediction set holds both "output 1 now" and
"b could still arrive" — held ambiguity again, resolved by whether more input comes.

## 7. Comparator (what changed?)

Train direction-of-change vocabulary, then present two multi-token frames
(before-state, after-state). Only the attribute pairs that were trained produce
predictions — the comparison falls out of the trie.

```python
hq = Hydraseq('_')
hq.insert('small large GROWING')
hq.insert('large small SHRINKING')
hq.insert('left right EAST')
hq.insert('right left WEST')

hq.look_ahead([['small', 'left', 'circle'], ['large', 'right', 'circle']])
hq.get_next_values()
# ['EAST', 'GROWING']
```

**Use it for:** describing deltas between structured states — Raven's-matrix-style
"what transformation happened?", diffing configurations, change summaries.

## 8. Span labeling with convolutions

Cap training sequences with a label prefixed by the instance uuid. `convolutions()`
then finds every labeled span in a stream, overlaps included; `get_paths()` chains
them into complete non-overlapping segmentations.

```python
hdr = Hydraseq('_')
hdr.insert("a b c _ALPHA")
hdr.insert("1 2 3 _DIGIT")

hdr.convolutions("a b c 1 2 3".split())
# [{'words': ['a','b','c'], 'start': 0, 'end': 3, 'convo': '_ALPHA'},
#  {'words': ['1','2','3'], 'start': 3, 'end': 6, 'convo': '_DIGIT'}]
```

**Use it for:** chunking a token stream into typed segments — the raw mechanism that
addrext used for address parts, before PatternScanner wrapped it cleanly.

## 9. Pattern scanning

`PatternScanner` = an encoder (raw token → category labels) + a Hydraseq trained on
label sequences capped with a concept. `get_markers` finds every span matching a
concept, even embedded mid-sentence.

```python
from hydraseq import Hydraseq, PatternScanner

COLORS, SIZES, FRUITS = {'red', 'green'}, {'big', 'small'}, {'apple', 'grape'}

def encoder(token):
    cats = []
    if token in COLORS: cats.append('COLOR')
    if token in SIZES:  cats.append('SIZE')
    if token in FRUITS: cats.append('FRUIT')
    return cats or ['OTHER']

seq = Hydraseq('items')
seq.insert([['SIZE'], ['COLOR'], ['FRUIT'], ['ITEM']])
seq.insert([['COLOR'], ['FRUIT'], ['ITEM']])

scanner = PatternScanner(seq, encoder)
scanner.get_markers("i bought big red apple yesterday", ['ITEM'])
# [Marker(start=2, end=5, length=3, labels=['ITEM'], text='big red apple'),
#  Marker(start=3, end=5, length=2, labels=['ITEM'], text='red apple')]
```

An encoder may return several labels for one token — that ambiguity is preserved in
the markers and resolved higher up (recipes 10–11).

**Use it for:** extracting typed entities from messy text — addresses, quantities,
dates — anything where category sequences identify a concept.

## 10. Layered scanning

Stack scanners: each layer's output labels are the next layer's input tokens. The
upper-layer encoder is just identity. Three proven levels: lexical → syntactic →
semantic ([test_sentence_scanner.py](../tests/test_sentence_scanner.py)).

```python
from hydraseq import LayeredScanner

# layer 1: raw words -> MODIFIER / FRUIT_SPAN;  layer 2: those -> ITEM
l1 = Hydraseq('l1')
l1.insert([['SIZE'], ['COLOR'], ['MODIFIER']])
l1.insert([['COLOR'], ['MODIFIER']])
l1.insert([['FRUIT'], ['FRUIT_SPAN']])
l2 = Hydraseq('l2')
l2.insert([['MODIFIER'], ['FRUIT_SPAN'], ['ITEM']])

layered = LayeredScanner(
    layers=[PatternScanner(l1, encoder), PatternScanner(l2, lambda t: [t])],
    intermediate_targets=[['MODIFIER', 'FRUIT_SPAN']])

layered.scan('big red apple', ['ITEM'])
# [Marker(start=0, end=2, length=2, labels=['ITEM'], text='MODIFIER FRUIT_SPAN')]
```

When a lower-layer marker carries several labels, `scan` fans out into one
interpretation per combination and carries all of them upward.

## 11. Closed-loop semantic resolution

The deepest recipe: make the top layer's grammar the semantic filter. Encode semantic
type into labels from layer 1 (`ANIMATE_PROPN`, `INANIMATE_NOUN`), carry it through
typed phrases (`ANIMATE_NP`), and train layer 3 **only on coherent** subject-verb-object
combinations. Incoherent pronoun bindings then simply fail to complete SENTENCE — no
filtering code exists anywhere.

An ambiguous pronoun encodes as multiple labels (recipe 5), fans out (recipe 10), and
only the coherent binding survives to the top. See
[test_closed_loop.py](../tests/test_closed_loop.py) and
[test_pronoun_layered.py](../tests/test_pronoun_layered.py) for the full worked
pipelines — they are too long to inline but each is a complete, commented example.

**Why it matters:** this is the project thesis in miniature — disambiguation without a
disambiguator. The structure does it.

## 12. Deduction by forward chaining

Train deduction steps as `"premise premise conclusion"` sequences. `forward_chain`
then queries every ordered subset of known facts, adds new predictions, and repeats
until stable — multi-step proofs with no manual chaining.

```python
from hydraseq import Hydraseq, forward_chain

logic = Hydraseq('logic')
for rule in ["alice=cat", "bob=coffee", "dog=milk",
             "alice=cat alice!=dog",
             "bob=coffee bob!=milk",
             "bob!=milk dog=milk bob!=dog",
             "alice!=dog bob!=dog carol=dog",
             "carol=dog dog=milk carol=milk",
             "bob=coffee carol=milk alice=tea",
             "alice=cat carol=dog bob=fish"]:
    logic.insert(rule)

known, iterations = forward_chain(logic, {'alice=cat', 'bob=coffee', 'dog=milk'})
# known ⊇ {'alice=tea', 'bob=fish', 'carol=dog', 'carol=milk', ...}   in 2 iterations
```

Three clues in, the full puzzle solution out — and no wrong facts appear.

## 13. Variables via role mapping

The generalization of recipe 12: train the reasoner ONCE on abstract roles
(`PERSON1=PET1 PERSON1!=PET2` ...), and use a `RoleMapper` to translate any concrete
puzzle in and out. The reasoner never sees the specific names — that's variable
binding with learned sequences.

```python
from hydraseq import solve_puzzle

role_map = {'xavier': 'PERSON1', 'yvonne': 'PERSON2', 'zara':   'PERSON3',
            'parrot': 'PET1',    'snake':  'PET2',    'turtle': 'PET3',
            'juice':  'DRINK1',  'soda':   'DRINK2',  'water':  'DRINK3'}

solve_puzzle(abstract_reasoner, role_map,
             {'xavier=parrot', 'yvonne=soda', 'snake=water'})
# {'xavier=juice', 'yvonne=turtle', 'zara=snake', 'zara=water', ...}
```

[test_abstract_reasoning.py](../tests/test_abstract_reasoning.py) solves three
differently-named puzzles with the same untouched reasoner instance.

**Use it for:** any problem family with fixed structure and varying fillers — the
role map is the only per-instance work.

## 14. Inference by analogy

When a query triggers surprise, don't fail — profile the unknown subject by what IS
known about it, find its nearest known neighbors, and ask them instead.
`infer_by_analogy` packages the whole loop.

```python
hdr = Hydraseq('main')
for line in open('tests/data/fox_eat_data_extended.txt'):
    hdr.insert(line)      # facts like "fox has fur", "coyote eat mice", ...

hdr.look_ahead("fox eat").surprise    # True — never told what foxes eat
hdr.infer_by_analogy("fox eat")
# ['mice', 'rabbit', 'rodent'] — fox shares fur+forest with coyote, so ask the coyote
```

**Use it for:** graceful degradation on unseen queries — recommendations, property
guessing, filling gaps in a knowledge base by similarity vote.

## 15. State machines

A DFA is a trained set of `"state event next_state"` transitions plus a cursor —
`DFAstate` wraps a Hydraseq into exactly that.

```python
from hydraseq import DFAstate

dfa = DFAstate(["s1 a s2", "s2 b s3", "s3 a,b s3"],
               init_state="s1", accepting_states=["s3"])

dfa.read_string("ab").in_accepting()   # True
dfa.read_string("aa").in_accepting()   # False
dfa.convert_to_mermaid()               # renderable state diagram
```

**Use it for:** protocol validation, input grammars, game logic — anywhere you'd
hand-write a state machine, but here the transition table is learnable data.

## 16. World knowledge + Winograd schemas

Load a fact base into an ordinary Hydraseq, then resolve pronoun references against
it. `resolve` tries increasingly general probes (raw bigrams → content bigrams →
post-pronoun words → whole sentence) and maps the triggering fact to a referent.

```python
import json
from hydraseq import load_world, resolve, evaluate_world

world = load_world()                       # 292 facts, domains like 'containment'
schemas = json.load(open('data/winograd_wsc.json'))

schemas[0]['text']
# 'The city councilmen refused the demonstrators a permit because they feared violence.'
resolve(schemas[0], world)
# ('A', 'feared')  — 'feared' points at the councilmen

evaluate_world(world, schemas)[0]
# 0.846  — 241/285 correct
```

The `reason` in the return value makes every resolution auditable — you can see which
learned fact decided it.

## 17. Attention / top-down gating

Restrict matching to the pathway of an expected concept — top-down expectation as a
filter, not a rule. Useful when context tells you what KIND of thing to look for
before the input arrives.

```python
hdr = Hydraseq('main')
hdr.insert("a b c d e f LETTERS")
hdr.insert("1 2 3 4 5 6 NUMBERS")

hdr.activate_node_pathway('LETTERS')          # expect letters
hdr.look_ahead("a b c d").get_next_values()   # ['e']
hdr.look_ahead("1 2 3 4").get_next_values()   # []  — numbers are gated off
hdr.reset_node_pathway()
hdr.look_ahead("1 2 3 4").get_next_values()   # ['5'] — back to normal
```

`set_active_synapses(['f'])` is the input-side variant: tokens unrelated to the
expected output are dropped before matching. See
[test_hydraseq.py](../tests/test_hydraseq.py) (`test_activate_node_pathway`,
`test_active_synapses`).
