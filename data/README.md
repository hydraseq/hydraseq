# Winograd Schema Challenge Data

## Source
Original WSC collection from Ernest Davis / Hector Levesque / Gary Marcus:
  https://cs.nyu.edu/~davise/papers/WinogradSchemas/WSCollection.xml

## Files
- `winograd_wsc.json` — 285 schemas, parsed from the official XML

## Schema format
Each entry:
```json
{
  "text":        "Full sentence with pronoun embedded",
  "pronoun":     "the ambiguous pronoun (he/she/it/they/...)",
  "option_a":    "first candidate referent",
  "option_b":    "second candidate referent",
  "correct":     "A or B",
  "discriminator": "the phrase that changes between the paired schema",
  "source":      "attribution"
}
```

Schemas come in pairs: same sentence, same options, one word changed —
that word is the discriminator that flips the correct answer.

## Category breakdown (138 pairs)

| Category | Pairs | % | Notes |
|---|---|---|---|
| Deep world knowledge | 121 | 87% | Requires associations not in sentence structure |
| Structurally tractable | 14 | 10% | Size/spatial/state/causal-role |
| Social/emotion | 3 | 2% | Requires social world model |

### Structurally tractable breakdown
- **SIZE/PHYSICAL** (8 schemas): "too large/small", "heavy/light", "made of steel/styrofoam"
- **SPATIAL** (7 pairs): "top/bottom", "above/below", "through/behind"
- **CAUSAL_ROLE** (3 pairs): "bought/sold", "punished/rescued"
- **STATE** (2 pairs): "before/after", "succeeded/lost"

### Key takeaway
The dataset was *designed* to require world knowledge — 87% cannot be solved
by structural or linguistic pattern matching alone. The ~10% tractable subset
is a valid starting point for hydraseq exploration, with the understanding
that hitting high overall accuracy requires encoding world knowledge as sequences.
