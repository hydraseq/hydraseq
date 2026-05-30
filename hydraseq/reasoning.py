"""
Forward chaining over a trained Hydraseq reasoner.

The reasoner is a Hydraseq trained on deduction chains where each sequence
ends with the conclusion: "premise1 premise2 conclusion".

forward_chain() repeatedly queries the reasoner with all ordered subsets of
known facts, collects new predictions, and iterates until no new facts emerge.
"""

from itertools import permutations


def _split_fact(fact):
    """Split 'alice=cat' into ('alice', '=', 'cat'), handles != too."""
    if '!=' in fact:
        left, right = fact.split('!=')
        return left, '!=', right
    left, right = fact.split('=')
    return left, '=', right


class RoleMapper:
    """Bidirectional translator between specific tokens and abstract role labels.

    Encodes facts like 'alice=cat' to 'PERSON1=PET1' and decodes back.
    The same abstract reasoner can then solve any puzzle — only the RoleMapper
    changes per puzzle instance.
    """

    def __init__(self, role_map):
        """
        Args:
            role_map: dict mapping specific tokens to role labels
                      e.g. {'alice': 'PERSON1', 'cat': 'PET1', ...}
        """
        self.to_role   = role_map
        self.from_role = {v: k for k, v in role_map.items()}

    def encode(self, fact):
        """'alice=cat' -> 'PERSON1=PET1'"""
        left, op, right = _split_fact(fact)
        return f"{self.to_role.get(left, left)}{op}{self.to_role.get(right, right)}"

    def decode(self, fact):
        """'PERSON1=PET1' -> 'alice=cat'"""
        left, op, right = _split_fact(fact)
        return f"{self.from_role.get(left, left)}{op}{self.from_role.get(right, right)}"

    def encode_all(self, facts):
        return {self.encode(f) for f in facts}

    def decode_all(self, facts):
        return {self.decode(f) for f in facts}


def solve_puzzle(abstract_reasoner, role_map, base_clues, **kwargs):
    """Solve a logic puzzle using an abstract reasoner and a role mapping.

    Args:
        abstract_reasoner:  a Hydraseq trained on role-level deduction rules
        role_map:           dict mapping specific tokens to abstract role labels
        base_clues:         set of specific-token fact strings (the given clues)
        **kwargs:           passed through to forward_chain

    Returns:
        set of specific-token facts representing the full derived solution
    """
    mapper = RoleMapper(role_map)
    abstract_clues    = mapper.encode_all(base_clues)
    abstract_solution, _ = forward_chain(abstract_reasoner, abstract_clues, **kwargs)
    return mapper.decode_all(abstract_solution)


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
