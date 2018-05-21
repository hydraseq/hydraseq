# hydraseq
Simple data structure to remember sequences

Data structure composed of a trie embedded in dictiories for easy lookup.  Basic function is to keep track of sequences given and then return the next expected in a sequence if already seen.

Example usage
```python
from hydraseq import Hydraseq

hdr = Hydraseq('main')

hdr.predict("The quick brown fox jumped over the lazy dog", is_learning=True)
assert hdr.predict("The quick brown").sdr_predicted == ['fox']

hdr.predict("The quick brown cat jumped over the lazy dog", is_learning=True)
assert hdr.predict("The quick brown").sdr_predicted == ['cat', 'fox']
```

# Some notes on usage
* The is_learning flag means it will remember this sequence.  This is so you can then use it later to check predicted next words in a read only mode.  Otherwise it would just remember all the tried sequences.
* The input is either a sentence which gets space separated, as in the example above, or it can also be a list.
    - When learning a new sequence as in the following example:
    
```python
    hdr = Hydraseq('main')

    hdr.predict([['a'], ['b', 'c'], ['d'], ['e']], is_learning=True)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 0

    hdr.predict([['a']], is_learning=False)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 2

    hdr.predict([['a'], ['b', 'f']], is_learning=False)
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 1


    hdr.predict([['a'], ['b', 'c'],['d']])
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 1
    assert hdr.sdr_predicted == ['e']


    hdr.predict([['a'], ['b']])
    assert len(hdr.active) == 1
    assert len(hdr.predicted) == 1
    assert hdr.sdr_predicted == ['d']
```
