import re
import sys
sys.path.append('./hydraseq')
from hydraseq import Hydraseq

# Testing an application of using hydraseq as a comparator.
# Could be useful in solving raven's matrices.  Once the patterns of change are
# inserted, a sequence of words results in those things that show directions of change.
#
# This is equivalent to forming the cartesian combinations from two groups of words,
# and then filtering for those a-b combinations which are known.  Except this is 
# more efficient since it only forms the cartesian combinations that have meaning to
# begin with
#
def test_compare():
    hq = Hydraseq('_')

    hq.insert('small large GROWING')
    hq.insert('large small SHRINKING')
    hq.insert('left right EAST')
    hq.insert('right left WEST')
    hq.insert('circle square SHAPER')
    hq.insert('square circle BLUNTER')

    hq.look_ahead([['small', 'left', 'circle'], ['small', 'right', 'circle']])
    assert hq.get_next_values() == ['EAST']

    hq.look_ahead([['small', 'left', 'square'], ['small', 'right', 'circle']])
    assert hq.get_next_values() == ['BLUNTER', 'EAST']

    hq.look_ahead([['small', 'left', 'circle'], ['large', 'right', 'circle']])
    assert hq.get_next_values() == ['EAST', 'GROWING']

    hq.look_ahead([['large', 'right', 'circle'], ['small', 'left', 'circle']])
    assert hq.get_next_values() == ['SHRINKING', 'WEST']


