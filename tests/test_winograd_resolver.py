"""
Winograd Schema resolver — full evaluation.

Tests:
  1. Sanity checks on individual known schemas
  2. In-sample accuracy (trained on all pairs, tested on same)
  3. Leave-one-out cross-validation (true generalization measure)
  4. Breakdown by discriminator type
  5. Error analysis — what does the resolver get wrong and why?
"""
import sys, json
sys.path.insert(0, '.')
from pathlib import Path
from collections import Counter, defaultdict

from hydraseq.winograd import (
    WinogradResolver, make_pairs, evaluate,
    discriminating_words, content_words, first_mentioned,
    leave_one_out_cv
)

DATA = Path('data/winograd_wsc.json')


def load():
    with open(DATA) as f:
        return json.load(f)


def make_full_resolver(schemas):
    resolver = WinogradResolver()
    for pair in make_pairs(schemas):
        resolver.train_pair(*pair)
    return resolver


# ── individual known schemas ───────────────────────────────────────────────────

def test_trophy_suitcase_large():
    """'too large' → trophy (option_a) is the referent."""
    schemas = load()
    pairs   = make_pairs(schemas)
    # train on all pairs
    resolver = make_full_resolver(schemas)
    # find the trophy schema
    trophy = next(s for s in schemas
                  if 'trophy' in s['text'] and 'large' in s['text'])
    assert resolver.predict(trophy) == trophy['correct']

def test_trophy_suitcase_small():
    """'too small' → suitcase (option_b) is the referent."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    suitcase = next(s for s in schemas
                    if 'trophy' in s['text'] and 'small' in s['text'])
    assert resolver.predict(suitcase) == suitcase['correct']

def test_councilmen_feared():
    """'feared' → councilmen (A) is the referent."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    s = next(s for s in schemas if 'councilmen' in s['text'] and 'feared' in s['text'])
    assert resolver.predict(s) == s['correct']

def test_councilmen_advocated():
    """'advocated' → demonstrators (B) is the referent."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    s = next(s for s in schemas if 'councilmen' in s['text'] and 'advocated' in s['text'])
    assert resolver.predict(s) == s['correct']

def test_ball_steel():
    """'made of steel' → ball (A) crashed through the table."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    s = next(s for s in schemas if 'ball' in s['text'] and 'steel' in s['text'])
    assert resolver.predict(s) == s['correct']

def test_ball_styrofoam():
    """'made of styrofoam' → table (B) is the weak one."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    s = next(s for s in schemas if 'ball' in s['text'] and 'styrofoam' in s['text'])
    assert resolver.predict(s) == s['correct']


# ── in-sample accuracy ─────────────────────────────────────────────────────────

def test_in_sample_accuracy():
    """In-sample: resolver trained on all pairs, tested on all schemas."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    acc, _ = evaluate(resolver, schemas)
    print(f"\nIn-sample accuracy: {acc:.1%}  (n={len(schemas)})")
    # Should be well above 50% — discriminator lookup should fire on most
    assert acc >= 0.65, f"Expected >= 65%, got {acc:.1%}"

def test_in_sample_vs_baseline():
    """Resolver should beat the first-mentioned baseline."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    resolver_acc, _ = evaluate(resolver, schemas)

    # first-mentioned baseline
    fm_correct = sum(1 for s in schemas if first_mentioned(s) == s['correct'])
    fm_acc = fm_correct / len(schemas)

    print(f"\nFirst-mentioned baseline: {fm_acc:.1%}")
    print(f"Resolver (in-sample):     {resolver_acc:.1%}")
    assert resolver_acc > fm_acc, "Resolver should beat first-mentioned baseline"


# ── leave-one-out cross-validation ────────────────────────────────────────────

def test_leave_one_out_accuracy():
    """
    LOO-CV: true generalization.  For each held-out pair, trained on the rest.
    This is the honest accuracy number.
    """
    schemas = load()
    acc = leave_one_out_cv(schemas)
    print(f"\nLeave-one-out CV accuracy: {acc:.1%}  (n={len(schemas)})")
    # Should beat coin-flip; beating first-mentioned baseline is the real goal
    assert acc >= 0.45, f"Expected >= 45%, got {acc:.1%}"
    print(f"  (beating 50% on LOO-CV is the hard target — requires generalization)")


# ── breakdown by discriminator type ───────────────────────────────────────────

SIZE_WORDS    = {'large','small','big','heavy','light','tall','short','fast','slow',
                 'strong','weak','wide','narrow','empty','full','steel','styrofoam'}
SPATIAL_WORDS = {'above','below','top','bottom','left','right','through','behind',
                 'inside','outside','up','down','over','under'}
STATE_WORDS   = {'before','after','succeeded','failed','won','lost','good','bad',
                 'better','worse','above','below'}
ROLE_WORDS    = {'gave','received','bought','sold','taught','learned',
                 'punished','rescued','convinced','understood'}

def pair_category(pair):
    a, b = pair
    diff = (set(a['text'].lower().split()) ^ set(b['text'].lower().split()))
    clean = {w.strip('.,!?;:') for w in diff}
    if clean & SIZE_WORDS:    return 'SIZE'
    if clean & SPATIAL_WORDS: return 'SPATIAL'
    if clean & STATE_WORDS:   return 'STATE'
    if clean & ROLE_WORDS:    return 'ROLE'
    return 'WORLD'

def test_accuracy_by_category():
    """Break down in-sample accuracy by discriminator type."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    pairs = make_pairs(schemas)

    by_cat = defaultdict(list)
    for pair in pairs:
        cat = pair_category(pair)
        for s in pair:
            pred = resolver.predict(s)
            by_cat[cat].append(pred == s['correct'])

    print("\nAccuracy by category (in-sample):")
    for cat in ['SIZE', 'SPATIAL', 'STATE', 'ROLE', 'WORLD']:
        if cat in by_cat:
            results = by_cat[cat]
            acc = sum(results) / len(results)
            print(f"  {cat:10s}: {acc:.1%}  ({len(results)} schemas)")

    # Tractable categories should be well above world-knowledge
    world_acc = sum(by_cat['WORLD']) / len(by_cat['WORLD']) if by_cat['WORLD'] else 0
    structural = [r for cat in ['SIZE','SPATIAL','STATE','ROLE'] for r in by_cat[cat]]
    struct_acc = sum(structural) / len(structural) if structural else 0
    print(f"\n  STRUCTURAL combined: {struct_acc:.1%}  ({len(structural)} schemas)")
    print(f"  WORLD:               {world_acc:.1%}  ({len(by_cat['WORLD'])} schemas)")


# ── error analysis ─────────────────────────────────────────────────────────────

def test_error_analysis():
    """Show what the resolver gets wrong and why."""
    schemas = load()
    resolver = make_full_resolver(schemas)
    _, results = evaluate(resolver, schemas)

    errors = [r for r in results if not r['ok']]
    print(f"\nErrors: {len(errors)} / {len(schemas)}")

    # Show first 10 errors with explanation
    for r in errors[:10]:
        s = r['schema']
        pred, reason = resolver.predict_explain(s)
        print(f"\n  TEXT: {s['text'][:85]}")
        print(f"  expected={s['correct']} ({s['option_a'] if s['correct']=='A' else s['option_b']})")
        print(f"  predicted={pred}  reason={reason}")

def test_discriminator_conflict_analysis():
    """
    Some discriminator words may appear in multiple pairs predicting DIFFERENT
    answers — these are unresolvable conflicts.
    """
    schemas = load()
    pairs   = make_pairs(schemas)

    from collections import defaultdict
    word_answers = defaultdict(set)
    for a, b in pairs:
        disc_a, disc_b = discriminating_words(a, b)
        for w in disc_a:
            word_answers[w].add(f"ANSWER_{a['correct']}")
        for w in disc_b:
            word_answers[w].add(f"ANSWER_{b['correct']}")

    conflicts = {w: ans for w, ans in word_answers.items() if len(ans) > 1}
    print(f"\nDiscriminator conflicts (word predicts BOTH A and B): {len(conflicts)}")
    for w, ans in list(conflicts.items())[:5]:
        print(f"  '{w}': {ans}")

    # Conflicts are a ceiling on discriminator-based accuracy
    total_discs = len(word_answers)
    print(f"Total unique discriminators: {total_discs}")
    print(f"Conflict-free:              {total_discs - len(conflicts)}")
