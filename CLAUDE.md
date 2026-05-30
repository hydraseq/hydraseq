# Hydraseq — Project Notes

## Core Philosophy

The guiding principle is: **no special rules, only learned sequences**. Every behavior
should emerge from the trie structure and trained sequences, not from hard-coded logic.
This is the only path to something that scales to genuinely useful language understanding.

Special-casing is the enemy. If a behavior requires an explicit rule, that's a signal
the representation is wrong — not that the rule is needed.

## What Hydraseq Is

A trie-based sequence memory. Each word occurrence in a sequence becomes a Node, linked
in chains. The same word in different contexts gets distinct Node instances. The structure
naturally handles:

- Branching (multiple continuations from the same prefix)
- Shared sub-sequences
- Held ambiguity (multiple active interpretations simultaneously)
- Hierarchical representations via the convolution/layers system

The core class (`Hydraseq`) should stay minimal. Higher-level behavior lives in
composable wrappers.

## Inspiration and aspiration of the project
Original inspiration from Jeff Hawking's On Intelligence hierarchical architecture

* A kind of neural network based on nodes and sequences, (tries), not layers of hidden neurons.
* Once we have enough data, attempt
    - inference WITHOUT backpropagation
    - no dependence on 'weights', but use Sparse Distributed Representation for
        - markov chain like calculations
        - probability
    - naturally distinguish bass (instrument versus fish) from context
    - planning, i.e. 'imagine' an outcome and create a plan

NB: A big inspiration was ironically a counter reaction to Domingo's book Master Algorithm.  I 
think what we need is the Master Data Structure, and I think hydraseqs are potentially capable
of being a starting point.  From it we should be able to do markov chains, bayes, analogical thinking,
inference, logic, symbol manipulation, variables.


## Surfaces Being Explored

The project has several distinct "surfaces" — ways the same core structure can be used:

### 1. Sequence Memory (core)
Basic insert/predict. Train on sequences, query what comes next.
`hdr.insert("the fox jumped")` → `hdr.look_ahead("the fox").get_next_values()` → `['jumped']`

### 2. Logic Gates
Boolean gates encoded as sequences. AND, OR, XOR, NAND all work.
NAND is universal (Turing complete), meaning Hydraseq has the raw ingredients
for arbitrary computation via learned sequences alone.
See: `tests/test_gates.py`

### 3. Analogy / Inference
`infer_by_analogy()` — when a query triggers surprise (unknown), profiles the subject
via known properties, finds similar known entities, and delegates the question to them.
See: `tests/test_cortical_experiment.py`, `fox_eat.py`

### 4. Pattern Scanner (PatternScanner)
Sliding window over token streams. An encoder maps raw tokens to category labels
(possibly multiple labels per token — the ambiguity is intentional and preserved).
A trained Hydraseq recognizes sequences of those labels capped with a concept token.
`get_markers()` finds all spans. `get_paths()` chains non-overlapping spans via BFS.
See: `hydraseq/scanner.py`, `tests/test_scanner.py`

### 5. Layered Scanner (LayeredScanner)
Stacks multiple PatternScanners so each layer's output labels become the next layer's
input tokens. Proven to scale to 3 levels (lexical → syntactic → semantic).
Each layer's encoder is just the identity function on the previous layer's output labels.
See: `hydraseq/scanner.py`, `tests/test_layered_scanner.py`, `tests/test_sentence_scanner.py`

### 6. Closed-Loop Semantic Resolution
The key insight: instead of a separate semantic resolver AFTER structural layers,
Layer 3 is trained ONLY on coherent subject-verb-object combinations. Incoherent
bindings fail to produce SENTENCE at Layer 3 — eliminated by the structure itself.
No external filtering code needed.
See: `tests/test_closed_loop.py`

### 7. Pronoun / Variable Resolution
Ambiguous tokens (IT, pronouns) encode as multiple category labels simultaneously —
exactly like 'st' in addrext (SAINT vs STREET). LayeredScanner fans out into parallel
interpretations via cartesian product of each marker's labels. Only the coherent
binding completes to SENTENCE. The resolution is internal to the pipeline.
See: `tests/test_pronoun_layered.py`, `tests/test_closed_loop.py`

## Key Architectural Decisions

### Ambiguity is a feature, not a bug
When a token maps to multiple categories, the scanner holds ALL interpretations
simultaneously. Premature disambiguation is wrong — the context at higher layers
is what legitimately resolves it. This mirrors how the brain likely works.

### LayeredScanner fan-out
When a marker has multiple labels, `LayeredScanner.scan()` uses cartesian product
to generate all possible label sequences and runs remaining layers for each.
For unambiguous tokens (single label) behavior is identical to before.
This was a critical fix — the earlier `labels[0]` approach silently dropped
interpretations before semantic resolution could see them.

### Semantic types thread through layers
To enable closed-loop resolution, semantic type must be encoded in the label itself
at Layer 1 (e.g. `ANIMATE_PROPN`, `INANIMATE_NOUN`) and carried through into
typed phrases at Layer 2 (`ANIMATE_NP`, `INANIMATE_NP`). Generic labels (just `NP`)
lose the information needed for Layer 3 to discriminate coherent from incoherent.

### The grammar IS the semantic resolver
Layer 3 trained only on coherent combinations means the grammar itself rejects
incoherent parses. No separate semantic checking layer is needed. This keeps the
architecture uniform — everything is sequences, all the way up.

## Related Repos

**addrext** — `/Users/praedator/Documents/COMICS/repos/addrext`

The address parser that proved the multi-level pattern recognition approach.
Two Hydraseq instances stacked:
- `seq` — recognizes token category sequences → ADDRESS, POBOX, SUITE, DIR labels
- `seq2` — validates that a combination of those labels is a KEEP (valid full address)

Key insight that transferred to hydraseq core: disambiguation of ambiguous tokens
(e.g. 'st' = SAINT vs STREET) happens because only one interpretation completes
a valid sequence path. The wrong interpretation leads to a dead end, not an error.

The PatternScanner and LayeredScanner in hydraseq are the generalization of what
addrext did for addresses. addrext should eventually be reimplemented as a consumer
of hydraseq's PatternScanner/LayeredScanner rather than reimplementing the machinery.

## Active Branches

- **master** — stable core
- **pattern_recognizer** — PatternScanner, LayeredScanner, fan-out fix, all new tests

## Test Coverage by Surface

| File | Surface |
|---|---|
| `test_hydraseq.py` | Core trie behavior |
| `test_automata.py` | DFA state machine |
| `test_gates.py` | Logic gates (AND, OR, XOR, NAND) |
| `test_logic_puzzle.py` | Deduction chains as sequences |
| `test_compare.py` | Sequence comparison |
| `test_autocomplete.py` | Autocomplete behavior |
| `test_scanner.py` | PatternScanner |
| `test_layered_scanner.py` | Two-level LayeredScanner |
| `test_sentence_scanner.py` | Three-level sentence recognition |
| `test_pronoun_resolution.py` | Pronoun disambiguation (external resolver) |
| `test_pronoun_layered.py` | Pronoun ambiguity through structural layers |
| `test_closed_loop.py` | Full closed-loop semantic resolution |
| `test_cortical_experiment.py` | Analogy / cortical experiment |

## Open Questions / Next Directions

- **Logic grid puzzles** — deduction chains work for simple cases; variable binding
  across clues (the "who owns the fish?" style) is the next hard problem. The
  LayeredScanner's multi-level simultaneous validity may be the mechanism.

- **addrext migration** — reimplementing addrext on top of PatternScanner/LayeredScanner
  would validate that the abstraction is complete and not leaking address-specific logic.

- **Forward chaining** — the logic puzzle tests show manual chaining of deduction steps.
  A forward-chaining loop that feeds predictions back as new inputs (until no new facts
  emerge) would make this automatic.

- **Animate/Inanimate is a proxy** — the real distinction is causal role (agent vs
  patient). The current ANIMATE/INANIMATE split works for the toy domain but real
  language assigns animacy metaphorically ("the company decided", "the wind threw").
  These would just be additional trained sequences, not special rules.
