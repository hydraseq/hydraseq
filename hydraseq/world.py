"""
World-knowledge loader for Hydraseq.

Loads atomic facts from data/world_knowledge.json and trains them
into a Hydraseq instance as sequences.  The result is a reusable
world model that can be queried before attempting pronoun resolution.

Usage:
    from hydraseq.world import load_world
    world = load_world()                    # all domains
    world = load_world('containment', 'physical_force')  # specific domains

    # query: what do we know about 'too_large'?
    world.look_ahead('too_large').get_next_values()
    # -> ['means', 'object_exceeds_container']
"""
import json
from pathlib import Path
from hydraseq import Hydraseq

_DEFAULT_PATH = Path(__file__).parent.parent / 'data' / 'world_knowledge.json'


def load_world(*domains, path=None):
    """
    Load world-knowledge facts into a Hydraseq instance.

    Args:
        *domains: optional domain names to load (e.g. 'containment', 'spatial').
                  If empty, loads all domains.
        path:     path to world_knowledge.json (defaults to data/world_knowledge.json)

    Returns:
        A trained Hydraseq instance containing the world model.
    """
    fpath = Path(path) if path else _DEFAULT_PATH
    with open(fpath) as f:
        data = json.load(f)

    world = Hydraseq('world')

    keys = [k for k in data if not k.startswith('_')]
    if domains:
        keys = [k for k in keys if k in domains]

    count = 0
    for domain in keys:
        for fact in data[domain]:
            world.insert(fact)
            count += 1

    return world


def list_domains(path=None):
    """Return available domain names in the world knowledge file."""
    fpath = Path(path) if path else _DEFAULT_PATH
    with open(fpath) as f:
        data = json.load(f)
    return [k for k in data if not k.startswith('_')]


def fact_count(path=None):
    """Return total number of facts across all domains."""
    fpath = Path(path) if path else _DEFAULT_PATH
    with open(fpath) as f:
        data = json.load(f)
    return sum(len(v) for k, v in data.items() if not k.startswith('_'))
