import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq

def expand(st):
    return list(map(lambda c: [c], st))

def test_autocomplete():
    ac = Hydraseq('auto')
    for name in [
            'efrain',
            'efrom',
            'efren',
            'ephrem',
            'efrainium'
            ]:
        ac.insert(expand(name+'$'))
    
    def autocomp(st):
        def _compact(seq):
            return "".join([c for c in seq[:-1]]).replace(' ', '')
        ac.look_ahead(expand(st))
        hits = ac.forward_prediction()
    
        hits = [_compact(hit.get_sequence()) for hit in hits]
        return hits
    
    hits = autocomp('efra')
    assert hits == ['efrainium', 'efrain']
