import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq

DATA_FILE = 'tests/data/fox_eat_data_extended.txt'

def load_hdr():
    hdr = Hydraseq('main')
    for line in open(DATA_FILE, 'r').readlines():
        hdr.insert(line)
    return hdr


def test_fox_eat_experiment():
    load_hdr()
    assert True


def test_infer_by_analogy_known_query():
    """A known query should return direct predictions without analogy."""
    hdr = Hydraseq('main')
    hdr.insert("cat eat salmon")
    hdr.insert("cat eat mice")

    result = hdr.infer_by_analogy("cat eat")
    assert sorted(result) == ['mice', 'salmon']


def test_infer_by_analogy_unknown_subject():
    """A completely unknown subject with no properties should return []."""
    hdr = Hydraseq('main')
    hdr.insert("cat eat salmon")

    result = hdr.infer_by_analogy("unicorn eat")
    assert result == []


def test_infer_by_analogy_fox_eat():
    """Fox shares fur+forest with coyote (score 2), only fur with wolf and cat (score 1).
    Max-only means only coyote is used as proxy — inferred foods are coyote's."""
    hdr = load_hdr()

    result = hdr.infer_by_analogy("fox eat")

    assert result != []
    # coyote is the sole max-score similar animal
    assert sorted(result) == ['mice', 'rabbit', 'rodent']
    # wolf and cat foods should not appear (they were outscored)
    assert 'squirrel' not in result
    assert 'salmon' not in result
