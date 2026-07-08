# hydraseq

A trie-based sequence memory. Train it on sequences of tokens; it predicts
continuations, holds ambiguous interpretations simultaneously, and flags novelty.

The guiding principle: **no special rules, only learned sequences**. Logic gates,
deduction, analogy, parsing, pronoun resolution — every behavior below emerges from
the same trie structure and trained sequences, not from hard-coded logic.

## Installation

```
pip install hydraseq
```

## Quick start

```python
from hydraseq import Hydraseq

hdr = Hydraseq('main')
hdr.insert("The quick brown fox jumped over the lazy dog")

hdr.look_ahead("The quick brown").get_next_values()
# ['fox']
```

Insert a second sentence with `wolf` in place of `fox` and the prediction branches:

```python
hdr.insert("The quick brown wolf jumped over the lazy dog")

hdr.look_ahead("The quick brown").get_next_values()
# ['fox', 'wolf']
```

`insert` learns; `look_ahead` queries without learning. Step token-by-token with
`hit()`, check the `surprise` flag for novelty, and pass a list of alternatives at any
position to hold multiple interpretations at once — see the docs below.

## Documentation

- **[docs/API.md](docs/API.md)** — every atomic call (`insert`, `hit`, `look_ahead`,
  `forward_prediction`, `convolutions`, ...) with verified examples.
- **[docs/RECIPES.md](docs/RECIPES.md)** — the meaningful combinations, each backed by
  a test file: what to build with the atoms.

## What it can do

Each capability is a recipe in [docs/RECIPES.md](docs/RECIPES.md), proven by tests:

| Capability | In short |
|---|---|
| Sequence memory | train on sequences, predict continuations |
| Streaming | advance one token at a time, predictions always current |
| Novelty detection | `surprise` flag — binary familiarity, no threshold |
| Autocomplete | roll predictions forward to all reachable completions |
| Held ambiguity | multiple interpretations alive until context resolves them |
| Logic gates | AND/OR/XOR/NAND as trained sequences (NAND ⇒ Turing-complete ingredients) |
| Comparison | describe what changed between two states |
| Pattern scanning | find typed spans in token streams (`PatternScanner`) |
| Layered parsing | stack scanners: lexical → syntactic → semantic (`LayeredScanner`) |
| Semantic resolution | incoherent parses die in the structure — no filter code |
| Forward chaining | multi-step deduction from trained inference rules |
| Variables | abstract role reasoner + `RoleMapper` solves whole puzzle families |
| Analogy | unknown subject? profile it, ask its nearest known neighbors |
| State machines | DFAs as trained transition sequences |
| Winograd schemas | pronoun resolution from a learned world model — 84.6% on WSC |

## Running the tests

```
pytest
```

The tests double as executable documentation — each file in
[tests/](tests/) demonstrates one surface of the structure.
