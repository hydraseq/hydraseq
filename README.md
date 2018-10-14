hydraseq
--------
Simple data structure to remember sequences

Data structure composed of a trie embedded in dictiories for easy lookup.  Keep track of sequences given and then return the next expected in a sequence if already seen.

## Installation
`pip install hydraseq`

## Example usage
Insert a sentence, and the query to see what the next word is if you submit part of the sentence.  This basically rewinds the sentence up to that point and looks up what the next word would be.
```python
from hydraseq import Hydraseq

hdr = Hydraseq('main')

hdr.insert("The quick brown fox jumped over the lazy dog")

print(hdr.look_ahead("The quick brown").get_next_values())
> ['fox']
```

If you now insert a similar sentence, say use `wolf` instead of `fox`, the look ahead will return both.
```python

hdr.insert("The quick brown wolf jumped over the lazy dog")

print(hdr.look_ahead("The quick brown").get_next_values())

> ['fox', 'wolf']
```

## Stepping through word by word
The look_ahead rewinds from the start and stops at the last word, this is not too efficient.  You can do a reset, rewinding the start and setp through word by word recovering which words are next.

```python
word = ["The"]
hdr.reset()
while word:
    print(word)
    word = hdr.hit(word[0]).get_next_values()

print(".")
>
>['The']
>['quick']
>['brown']
>['fox', 'wolf']
>['jumped']
>['over']
>['the']
>['lazy']
>['dog']
>.
```

## Checking state, without actually inserting new words.
Every time you use `insert` the sequence is remembered.  If you just want to check what is next but make sure the insert doesn't cause new words to get remembered use the `is_learning=False` flag for both `insert` and `hit`
