# Hydraseq API Reference

The atomic calls. For meaningful combinations of these calls — the recipes — see
[RECIPES.md](RECIPES.md).

Everything here was executed against the current code; outputs shown are real.

---

## The mental model

A `Hydraseq` is a trie of `Node`s. Every word occurrence in a trained sequence becomes
its own Node — the same word in different contexts gets distinct Node instances. At any
moment the instance holds three pieces of state:

| State | Meaning |
|---|---|
| `active_nodes` | where you are — nodes matching the sequence consumed so far |
| `next_nodes` | what's predicted — every node reachable one step forward |
| `surprise` | `True` if the last input fell off all known paths |

Every query method returns `self`, so calls chain:
`hdr.look_ahead("the quick").get_next_values()`.

### Input formats

Methods that take a sequence accept either form:

```python
hdr.insert("the quick brown fox")               # string: split on whitespace
hdr.insert([['the'], ['quick'], ['brown']])     # list of frames
```

The list form is a **list of frames**, where each frame is a list of tokens active at
that step. A frame with more than one token means "either of these" — this is how
ambiguity enters the structure and it is the native format; strings are just the
convenient single-token-per-frame shorthand.

```python
hdr.insert([['a'], ['b'], ['d']])
hdr.insert([['a'], ['c'], ['d']])
hdr.look_ahead([['a'], ['b', 'c']])   # 'b' OR 'c' in second position
hdr.get_active_values()               # ['b', 'c']   — both interpretations held
hdr.get_active_sequences()            # ['a b', 'a c']
hdr.get_next_values()                 # ['d']        — both converge on d
```

---

## Constructor

```python
Hydraseq(uuid, hydraseq=None, rex=None)
```

| Arg | Purpose |
|---|---|
| `uuid` | name for this instance; `convolutions()` uses it as the output-label prefix |
| `hydraseq` | clone mode: share another instance's trained trie, fresh cursor state |
| `rex` | regex used by `get_word_array` to tokenize strings, e.g. `r"[\w']+"` |

```python
hdr0 = Hydraseq('zero')
hdr0.insert("the quick brown fox")
hdr1 = Hydraseq('one', hdr0)        # same memory, independent position
```

Cloning is cheap (no copy of the trie) — `convolutions()` uses one clone per window
position to run many simultaneous cursors over shared memory.

---

## Training

### `insert(sequence, is_learning=True)`
Learn a sequence (or with `is_learning=False`, just replay it — see `look_ahead`).
Resets state, then consumes the sequence one frame at a time. New transitions create
new Nodes and set `surprise = True`. Returns `self`.

### `load_from_file(fpath)`
Calls `insert` on each line of a text file. Returns `self`.

```python
hdr = Hydraseq('main')
for line in open('tests/data/fox_eat_data_extended.txt'):
    hdr.insert(line)
```

### `self_insert(sequence)` / `full_insert(sentence)`
Experimental auto-labeling: for each novel prefix, inserts the prefix capped with a
generated label `_N`. `full_insert` does this for every suffix of the sentence.
Gives every learned chunk an addressable name.

---

## Querying

### `look_ahead(sequence)`
`insert` with `is_learning=False`: replays the sequence from the start **without
learning**, leaving `active_nodes`/`next_nodes`/`surprise` set. This is the main
query call.

```python
hdr = Hydraseq('main')
hdr.insert("the quick brown fox jumped over the lazy dog")
hdr.insert("the quick brown wolf jumped over the lazy dog")

hdr.look_ahead("the quick brown").get_next_values()
# ['fox', 'wolf']
```

### `hit(lst_words, is_learning=True)`
Advance ONE step. Takes a single frame (list of tokens). Use after `reset()` or a
`look_ahead` to continue stepping without replaying from the start.

```python
hdr.reset()
hdr.look_ahead("the").get_next_values()                  # ['quick']
hdr.hit(["quick"], is_learning=False).get_next_values()  # ['brown']
```

With `is_learning=True` (default) the frame must be a single token and unknown
transitions grow the trie; with `False` unknown transitions just set `surprise`.

### `reset()`
Return the cursor to the root: active is the init node, predicted is every
sequence-initial token. Clears `surprise`. Returns `self`.

### Reading the state

| Call | Returns |
|---|---|
| `get_active_values()` | sorted unique keys of active nodes |
| `get_active_sequences()` | full path string for each active node |
| `get_next_values()` | sorted unique keys of predicted nodes |
| `get_next_sequences()` | full path string for each predicted node |
| `get_last_active_values()` / `..._sequences()` | the previous step's actives |
| `surprise` | `True` if the last frame matched no known continuation |

```python
hdr.look_ahead("the quick brown").get_next_sequences()
# ['the quick brown fox', 'the quick brown wolf']
```

### `forward_prediction()`
From the current predicted set, roll forward to all reachable **end nodes** (leaves).
Answers "where could this eventually lead?" rather than "what comes next?".
Returns a list of `Node`s — use `node.get_sequence()` to read each full path.
This is the autocomplete primitive (see recipes).

### `infer_by_analogy(partial_sequence)`
If the query is known, behaves like `look_ahead(...).get_next_values()`. If it triggers
surprise, profiles the unknown subject (first token) by its known properties, finds the
known entities sharing the most properties, re-asks the question of them, and returns
their answers ranked by vote. Returns `[]` when nothing is known about the subject.

```python
hdr.look_ahead("fox eat").surprise    # True — never trained
hdr.infer_by_analogy("fox eat")       # ['mice', 'rabbit', 'rodent'] — via coyote
```

---

## Span recognition (convolutions)

These use the convention that trained sequences end in a label token prefixed with the
instance's `uuid` (e.g. uuid `'_'` and labels `_ALPHA`, `_DIGIT`).

### `convolutions(words, as_json=True)`
Slide over the input and report every span that completes a trained sequence ending in
a `uuid`-prefixed label. Overlapping spans are all reported — ambiguity is preserved.

```python
hdr = Hydraseq('_')
hdr.insert("a b c _ALPHA")
hdr.insert("1 2 3 _DIGIT")
hdr.convolutions("a b c 1 2 3".split())
# [{'words': ['a','b','c'], 'start': 0, 'end': 3, 'convo': '_ALPHA'},
#  {'words': ['1','2','3'], 'start': 3, 'end': 6, 'convo': '_DIGIT'}]
```

### `convolutions_dict(words)`
Same results grouped into a dict keyed by span start — the adjacency structure for
path search.

### `get_paths(words)`
BFS over `convolutions_dict`: chains spans that tile end-to-start into complete
non-overlapping paths. Each path is one way to fully segment the input into labels.

### `end_points(sent, stop='0_')`
Repeatedly re-parse: get paths, join their labels into a new sentence, parse again with
the next uuid level (`0_` → `1_` → `2_`…) until reaching `stop`. A single-instance
version of layer stacking (the `PatternScanner`/`LayeredScanner` classes below are the
cleaner multi-instance form).

---

## Attention / gating

Two mechanisms restrict which nodes may activate — top-down expectation.

### `activate_node_pathway(top_words)` / `reset_node_pathway()`
Restrict all matching to nodes on paths that lead to `top_words`. Everything else goes
dark until reset.

```python
hdr = Hydraseq('main')
hdr.insert("a b c d e f LETTERS")
hdr.insert("1 2 3 4 5 6 NUMBERS")

hdr.activate_node_pathway('LETTERS')
hdr.look_ahead("a b c d").get_next_values()   # ['e']
hdr.look_ahead("1 2 3 4").get_next_values()   # []  — not on the LETTERS pathway
hdr.reset_node_pathway()
hdr.look_ahead("1 2 3 4").get_next_values()   # ['5']
```

### `set_active_synapses(out_words)` / `reset_active_synapses()`
Same idea at the input: incoming tokens not associated with `out_words` (via
`get_downwards`) are filtered before matching.

### `get_downwards(words)`
The support of a label: every input token appearing on any path that reaches `words`.

```python
hdr.get_downwards(["LETTERS"])   # ['a', 'b', 'c', 'd', 'e', 'f']
```

---

## Introspection

| Call | Returns |
|---|---|
| `get_node_count()` | `(number_of_columns, total_nodes)` |
| `get_word_array(str)` | tokenized frames, honoring the `rex` argument |
| `d_depths` | dict: depth → set of nodes at that depth |
| `columns` | dict: token → set of Nodes (all contexts that token appears in) |

### `Node`
`node.key` (the token), `node.nexts` / `node.lasts` (links), `node.depth`,
`node.get_sequence()` (full path string from root), `node.get_sequence_nodes()`
(the path as node lists).

---

## Companion classes and functions

All importable from the top-level package:

```python
from hydraseq import (Hydraseq, Node, DFAstate,
                      PatternScanner, LayeredScanner, Marker,
                      forward_chain, RoleMapper, solve_puzzle,
                      load_world, list_domains, fact_count,
                      resolve, evaluate_world)
```

### `PatternScanner(seq, encoder, tokenizer=None)` — [scanner.py](../hydraseq/scanner.py)
Sliding-window recognizer. `encoder(token) -> list[str]` maps raw tokens to category
labels (multiple labels = held ambiguity); `seq` is a Hydraseq trained on label
sequences capped with a concept token.

- `get_markers(sentence, targets)` → list of `Marker(start, end, length, labels, text)`
  for every span that predicts a target concept.
- `get_paths(markers)` → chains non-overlapping markers into complete parses.

### `LayeredScanner(layers, intermediate_targets)` — [scanner.py](../hydraseq/scanner.py)
Stacks PatternScanners: each layer's output labels are the next layer's input tokens.
`scan(tokens, final_targets)` runs the whole stack; ambiguous markers fan out via
cartesian product so every interpretation reaches the top, where only coherent ones
survive. Proven to 3 layers (lexical → syntactic → semantic).

### `DFAstate(transitions, init_state, accepting_states=[])` — [automata.py](../hydraseq/automata.py)
A finite state machine encoded as sequences (`"s1 a s2"` = from s1, on event a, go
to s2). `event(e)`, `read_string(s)`, `in_accepting()`, `get_active_states()`,
`convert_to_mermaid()` for diagrams.

### `forward_chain(reasoner, base_facts, max_premise_length=2, max_iterations=20)` — [reasoning.py](../hydraseq/reasoning.py)
Derive everything reachable from `base_facts` in a reasoner trained on
`"premise premise conclusion"` sequences. Iterates until no new facts emerge.
Returns `(known_facts, iterations)`.

### `RoleMapper(role_map)` / `solve_puzzle(abstract_reasoner, role_map, base_clues)` — [reasoning.py](../hydraseq/reasoning.py)
Variable binding. `RoleMapper` translates `'alice=cat'` ⇄ `'PERSON1=PET1'`;
`solve_puzzle` encodes the clues to roles, forward-chains in the abstract reasoner,
and decodes the solution back. One abstract reasoner solves every structurally
identical puzzle.

### `load_world(*domains, path=None)` / `list_domains()` / `fact_count()` — [world.py](../hydraseq/world.py)
Load [data/world_knowledge.json](../data/world_knowledge.json) (292 facts across
domains like `containment`, `physical_force`, `size_relations`) into a Hydraseq.
The result is an ordinary instance — query it with `look_ahead`.

### `resolve(schema, world)` / `evaluate_world(world, schemas)` — [winograd.py](../hydraseq/winograd.py)
Winograd Schema resolution against a loaded world model. `resolve` returns
`(answer, reason)`; `evaluate_world` returns `(accuracy, results)`.
Currently 84.6% on the 285-schema WSC set in
[data/winograd_wsc.json](../data/winograd_wsc.json).
`winograd.py` also exposes the earlier `WinogradResolver` (train/predict on schema
pairs) and `leave_one_out_cv` for generalization measurement.
