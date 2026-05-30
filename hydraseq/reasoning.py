"""
Forward chaining over a trained Hydraseq reasoner.

The reasoner is a Hydraseq trained on deduction chains where each sequence
ends with the conclusion: "premise1 premise2 conclusion".

forward_chain() repeatedly queries the reasoner with all ordered subsets of
known facts, collects new predictions, and iterates until no new facts emerge.
"""

from itertools import permutations


def forward_chain(reasoner, base_facts, max_premise_length=2, max_iterations=20):
    """Derive all facts reachable from base_facts by forward chaining.

    At each iteration, tries every ordered subset of known facts (up to
    max_premise_length) as a look_ahead query. Any new prediction is added
    to the known set and the process repeats until stable.

    Args:
        reasoner:           a trained Hydraseq instance
        base_facts:         iterable of initial fact strings
        max_premise_length: max number of premises to combine per query
        max_iterations:     safety limit on iterations

    Returns:
        (known, iterations) where known is the full set of derived facts
        and iterations is how many rounds it took to stabilise
    """
    known = set(base_facts)

    for iteration in range(max_iterations):
        new_facts = set()

        for length in range(1, max_premise_length + 1):
            for premise_seq in permutations(known, min(length, len(known))):
                query = " ".join(premise_seq)
                predictions = reasoner.look_ahead(query).get_next_values()
                for pred in predictions:
                    if pred not in known:
                        new_facts.add(pred)

        if not new_facts:
            return known, iteration

        known.update(new_facts)

    return known, max_iterations
