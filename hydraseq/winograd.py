"""
Winograd Schema resolver built on Hydraseq.

Core insight from dataset analysis:
  - 97% of correct referents appear BEFORE the pronoun in the sentence
  - Each schema pair differs by exactly one discriminating word
  - The discriminating word flips the answer between A and B

Resolution strategy:
  1. DEFAULT: predict the referent that appears BEFORE the pronoun
     (correct 97% of the time IF we can identify which schema variant we're in)
  2. DISCRIMINATOR LOOKUP: for each content word in the sentence,
     check if it is a trained discriminator that predicts A or B
  3. FALLBACK: nearest-candidate (coin flip ~50%)

Training: for each schema pair, the two differing words are extracted and
trained as: (discriminator_word → ANSWER_A) or (discriminator_word → ANSWER_B).
At test time, any content word matching a trained discriminator overrides
the default.

Cross-validation is used to measure true generalization (held-out pairs).
"""
import re
from hydraseq import Hydraseq


_STOP = {'the', 'a', 'an', 'is', 'was', 'were', 'had', 'have', 'has', 'be',
         'to', 'of', 'in', 'on', 'at', 'it', 'he', 'she', 'they', 'we',
         'i', 'you', 'him', 'her', 'them', 'his', 'its', 'their', 'our',
         'not', 'but', 'and', 'or', 'so', 'that', 'this', 'with', 'for',
         'from', 'by', 'as', 'up', 'if', 'do', 'did', 'does', 'been',
         'all', 'no', 'can', 'could', 'would', 'should', 'will',
         'because', 'although', 'even', 'though', 'when', 'after', 'before',
         'into', 'onto', 'upon', 'out', 'about', 'just', 'more', 'very',
         'still', 'also', 'then', 'than', 'too', 'only', 'such', 'much',
         'many', 'any', 'each', 'both', 'while', 'whose', 'which', 'who',
         'what', 'where', 'how', 'why', 'same', 'other', 'own', 'made'}


def clean_word(w):
    return re.sub(r"[^a-z'_-]", '', w.lower())


def content_words(text):
    return [cw for w in text.split() if (cw := clean_word(w)) and cw not in _STOP]


def pronoun_position(text, pronoun):
    """Return the character index of the pronoun as a whole word (not substring)."""
    pron = re.escape(pronoun.strip())
    # search for the LAST occurrence as a whole word (the pronoun, not e.g. "it" in "into")
    matches = list(re.finditer(r'\b' + pron + r'\b', text, re.IGNORECASE))
    if not matches:
        return -1
    # prefer the later occurrence (the anaphoric pronoun, not a nominal)
    return matches[-1].start()


def post_pronoun_words(schema):
    """Content words in the clause AFTER the pronoun — the discriminating zone."""
    text   = schema['text']
    pronoun = schema['pronoun'].strip()
    pos    = pronoun_position(text, pronoun)
    if pos < 0:
        return content_words(text)
    after  = text[pos + len(pronoun):]
    # take up to end of sentence or first major clause boundary
    clause = re.split(r'(?<=[.!?])\s', after)[0]
    return content_words(clause)


def discriminating_words(schema_a, schema_b):
    """
    Words unique to each schema in a pair, restricted to the post-pronoun clause.
    Using the post-pronoun clause avoids false positives from earlier in the sentence
    (e.g. 'it' inside 'into' being found before the actual pronoun).
    """
    wa = set(post_pronoun_words(schema_a))
    wb = set(post_pronoun_words(schema_b))
    return wa - wb, wb - wa   # disc_a, disc_b


def first_mentioned(schema):
    """Return 'A' if option_a appears before option_b in the text, else 'B'."""
    text = schema['text'].lower()
    key_a = schema['option_a'].lower().split()[-1]
    key_b = schema['option_b'].lower().split()[-1]
    pos_a = text.find(key_a)
    pos_b = text.find(key_b)
    if pos_a < 0:
        return 'B'
    if pos_b < 0:
        return 'A'
    return 'A' if pos_a <= pos_b else 'B'


class WinogradResolver:
    """
    Hydraseq-based Winograd Schema resolver.

    Training: call train_pair() for each (schema_a, schema_b) pair.
    Inference: call predict(schema) → 'A' or 'B'.
    """

    def __init__(self, name='winograd'):
        self.hdr = Hydraseq(name)
        self._trained_discs = set()   # track which words are discriminators

    def train_pair(self, schema_a, schema_b):
        """Learn from one schema pair."""
        disc_a, disc_b = discriminating_words(schema_a, schema_b)
        for w in disc_a:
            # only register if not already predicting the opposite answer
            existing = self.hdr.look_ahead(w).get_next_values()
            if f"ANSWER_{'B' if schema_a['correct']=='A' else 'A'}" not in existing:
                self.hdr.insert(f"{w} ANSWER_{schema_a['correct']}")
                self._trained_discs.add(w)
        for w in disc_b:
            existing = self.hdr.look_ahead(w).get_next_values()
            if f"ANSWER_{'B' if schema_b['correct']=='A' else 'A'}" not in existing:
                self.hdr.insert(f"{w} ANSWER_{schema_b['correct']}")
                self._trained_discs.add(w)

    def predict(self, schema):
        """
        Predict 'A' or 'B' for a single schema.

        Resolution order:
          1. Discriminator lookup in post-pronoun clause only
          2. First-mentioned heuristic
        """
        words = post_pronoun_words(schema)

        # 1. discriminator lookup
        for word in words:
            if word not in self._trained_discs:
                continue
            preds = self.hdr.look_ahead(word).get_next_values()
            if 'ANSWER_A' in preds:
                return 'A'
            if 'ANSWER_B' in preds:
                return 'B'

        # 2. first-mentioned fallback
        return first_mentioned(schema)

    def predict_explain(self, schema):
        """Like predict() but returns (answer, reason_string)."""
        words = post_pronoun_words(schema)
        for word in words:
            if word not in self._trained_discs:
                continue
            preds = self.hdr.look_ahead(word).get_next_values()
            if 'ANSWER_A' in preds:
                return 'A', f"discriminator '{word}' → A"
            if 'ANSWER_B' in preds:
                return 'B', f"discriminator '{word}' → B"
        fm = first_mentioned(schema)
        return fm, f"first-mentioned fallback → {fm}"


# ── evaluation helpers ────────────────────────────────────────────────────────

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


def evaluate(resolver, schemas):
    """Return accuracy and per-schema details."""
    correct = 0
    results = []
    for s in schemas:
        pred = resolver.predict(s)
        ok = pred == s['correct']
        correct += ok
        results.append({'schema': s, 'pred': pred, 'ok': ok})
    return correct / len(schemas), results


def leave_one_out_cv(schemas):
    """
    Leave-one-pair-out cross-validation.

    For each held-out pair, trains on all other pairs and tests on the
    two schemas in the held-out pair.  Returns overall accuracy.
    """
    pairs = make_pairs(schemas)
    correct_total = 0
    total = 0

    for i, held_out in enumerate(pairs):
        resolver = WinogradResolver(f'cv_{i}')
        # train on all pairs except held-out
        for j, pair in enumerate(pairs):
            if j == i:
                continue
            resolver.train_pair(*pair)
        # test on held-out pair
        for schema in held_out:
            pred = resolver.predict(schema)
            correct_total += (pred == schema['correct'])
            total += 1

    return correct_total / total
