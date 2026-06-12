"""
Winograd Schema Challenge — exploratory analysis.

Goal: understand what hydraseq can and cannot resolve, starting with the
structurally tractable subset (~10% of WSC273).

The 285 schemas come in pairs.  One word changes between the two versions
of a pair — that word is the discriminator that flips the correct answer.

Categories:
  STRUCTURAL  — size/spatial/state/causal-role: discriminator is in
                the sentence structure itself  (≈14 pairs / 10%)
  WORLD       — requires world knowledge not present in the sentence (≈87%)

This file:
  1. Loads the dataset
  2. Identifies the tractable subset
  3. Runs a simple baseline: "nearest candidate" heuristic
  4. Shows where hydraseq's pronoun-resolution machinery applies
"""
import sys, json, os
sys.path.insert(0, '.')
from pathlib import Path

DATA = Path(__file__).parent.parent / 'data' / 'winograd_wsc.json'


def load_schemas():
    with open(DATA) as f:
        return json.load(f)


def make_pairs(schemas):
    """Group consecutive schemas that share the same option_a / option_b."""
    pairs = []
    i = 0
    while i < len(schemas) - 1:
        a, b = schemas[i], schemas[i + 1]
        if a['option_a'] == b['option_a'] and a['option_b'] == b['option_b']:
            pairs.append((a, b))
            i += 2
        else:
            i += 1
    return pairs


SIZE_WORDS    = {'large','small','big','heavy','light','tall','short','fast','slow',
                 'strong','weak','wide','narrow','long','empty','full','steel','styrofoam'}
SPATIAL_WORDS = {'above','below','top','bottom','left','right','through','behind',
                 'front','back','inside','outside','up','down','over','under'}
STATE_WORDS   = {'before','after','succeeded','failed','won','lost'}
ROLE_WORDS    = {'gave','received','bought','sold','taught','learned',
                 'punished','rescued','convinced','understood'}

def pair_category(pair):
    a, b = pair
    diff = (set(a['text'].lower().split()) ^ set(b['text'].lower().split()))
    if diff & SIZE_WORDS:    return 'SIZE'
    if diff & SPATIAL_WORDS: return 'SPATIAL'
    if diff & STATE_WORDS:   return 'STATE'
    if diff & ROLE_WORDS:    return 'ROLE'
    return 'WORLD'


# ── dataset stats ─────────────────────────────────────────────────────────────

def test_dataset_loaded():
    schemas = load_schemas()
    assert len(schemas) == 285, f"Expected 285, got {len(schemas)}"

def test_pairs_identified():
    pairs = make_pairs(load_schemas())
    assert len(pairs) == 138, f"Expected 138 pairs, got {len(pairs)}"

def test_tractable_subset_size():
    """About 10% of pairs are structurally tractable."""
    pairs = make_pairs(load_schemas())
    tractable = [p for p in pairs if pair_category(p) != 'WORLD']
    # should be at least 10 pairs
    assert len(tractable) >= 10, f"Only {len(tractable)} tractable pairs found"
    print(f"\nTractable pairs: {len(tractable)} / {len(pairs)}")
    from collections import Counter
    cats = Counter(pair_category(p) for p in tractable)
    for cat, n in cats.most_common():
        print(f"  {cat}: {n}")

def test_pronoun_distribution():
    """Most schemas use 'it', 'he', 'she', 'they'."""
    from collections import Counter
    schemas = load_schemas()
    counts = Counter(s['pronoun'].lower().strip() for s in schemas)
    # 'it' and 'he' should dominate
    assert counts['it'] > 50
    assert counts['he'] > 50
    print(f"\nPronoun counts: {dict(counts.most_common())}")


# ── baseline: nearest-candidate heuristic ────────────────────────────────────
# The naive heuristic: the pronoun refers to the most recently mentioned noun.
# This is the simplest possible "model" — a useful lower bound.

def nearest_candidate_guess(schema):
    """Return 'A' or 'B' based on which option appears last in the text."""
    text  = schema['text'].lower()
    opt_a = schema['option_a'].lower()
    opt_b = schema['option_b'].lower()
    # find last occurrence of first word of each option
    key_a = opt_a.split()[-1]
    key_b = opt_b.split()[-1]
    pos_a = text.rfind(key_a)
    pos_b = text.rfind(key_b)
    # whichever is closer to the pronoun position wins
    pron  = schema['pronoun'].lower()
    pron_pos = text.rfind(pron)
    if pos_a < 0 and pos_b < 0:
        return 'A'
    if pos_a < 0:
        return 'B'
    if pos_b < 0:
        return 'A'
    # nearest = whichever candidate is closest to the pronoun
    if abs(pron_pos - pos_a) <= abs(pron_pos - pos_b):
        return 'A'
    return 'B'

def test_nearest_baseline_overall():
    """Nearest-candidate baseline accuracy on full dataset."""
    schemas = load_schemas()
    correct = sum(1 for s in schemas if nearest_candidate_guess(s) == s['correct'])
    acc = correct / len(schemas)
    print(f"\nNearest baseline accuracy (full, n={len(schemas)}): {acc:.1%}")
    # Should be around 50% (random) ± a few points
    assert 0.40 <= acc <= 0.65

def test_nearest_baseline_tractable():
    """Nearest-candidate accuracy on structurally tractable pairs only."""
    schemas = load_schemas()
    pairs   = make_pairs(schemas)
    tractable = [p for p in pairs if pair_category(p) != 'WORLD']
    flat = [s for p in tractable for s in p]
    correct = sum(1 for s in flat if nearest_candidate_guess(s) == s['correct'])
    acc = correct / len(flat)
    print(f"\nNearest baseline (tractable, n={len(flat)}): {acc:.1%}")

def test_nearest_baseline_world():
    """Nearest-candidate accuracy on world-knowledge pairs."""
    schemas = load_schemas()
    pairs   = make_pairs(schemas)
    world = [p for p in pairs if pair_category(p) == 'WORLD']
    flat = [s for p in world for s in p]
    correct = sum(1 for s in flat if nearest_candidate_guess(s) == s['correct'])
    acc = correct / len(flat)
    print(f"\nNearest baseline (world-knowledge, n={len(flat)}): {acc:.1%}")


# ── what a hydraseq approach looks like ──────────────────────────────────────
# For the SIZE category, the discriminating knowledge is:
#   "X doesn't fit in Y because X is too large"  → pronoun refers to X (the larger)
#   "X doesn't fit in Y because Y is too small"  → pronoun refers to Y (the smaller)
#
# This is exactly the closed-loop semantic resolution pattern:
#   Layer 1: map "too large/small" → SIZE_CAUSE label
#   Layer 2: map noun phrases + SIZE_CAUSE → typed phrase
#   Layer 3: trained only on coherent (pronoun_referent, SIZE_CAUSE) pairs
#
# For a quick proof-of-concept, we can encode it as a sequence rule:

def test_size_schemas_identified():
    """Identify the size/fit schemas we'll tackle first."""
    schemas = load_schemas()
    pairs   = make_pairs(schemas)
    size_pairs = [p for p in pairs if pair_category(p) == 'SIZE']
    print(f"\nSIZE schemas ({len(size_pairs)} pairs):")
    for a, b in size_pairs:
        print(f"  '{a['text'][:70]}...'")
        print(f"    discriminator: '{a['discriminator']}'  correct={a['correct']} → {a['option_a']}")
    assert len(size_pairs) >= 2

def test_size_rule_as_sequence():
    """
    Proof-of-concept: a Hydraseq trained on size/fit causal rules can
    resolve the trophy/suitcase pair.

    Rule encoding:
        "CONTAINER CONTENT too_large → CONTENT is referent"
        "CONTAINER CONTENT too_small → CONTAINER is referent"
    """
    from hydraseq import Hydraseq

    hdr = Hydraseq('size_rules')
    # Train: when X doesn't fit into Y because X is too large → X is referent
    hdr.insert("too_large CONTENT_referent")
    hdr.insert("too_small CONTAINER_referent")
    hdr.insert("made_of_hard SUBJECT_referent")
    hdr.insert("made_of_soft SUBJECT_referent")

    # trophy/suitcase: "doesn't fit because it is too large" → trophy (CONTENT)
    # option_a = trophy, option_b = suitcase
    result_large = hdr.look_ahead("too_large").get_next_values()
    result_small = hdr.look_ahead("too_small").get_next_values()

    assert 'CONTENT_referent'   in result_large, f"got {result_large}"
    assert 'CONTAINER_referent' in result_small, f"got {result_small}"

    # Now apply: for the trophy schema,
    # "it is too large" → CONTENT_referent → option_a (trophy) is the answer
    referent_map = {
        'CONTENT_referent':   'A',  # trophy is the content
        'CONTAINER_referent': 'B',  # suitcase is the container
    }
    assert referent_map[result_large[0]] == 'A'  # trophy → A
    assert referent_map[result_small[0]] == 'B'  # suitcase → B
