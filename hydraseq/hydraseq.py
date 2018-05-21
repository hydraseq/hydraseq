"""
180426-1346
Basic Memory Data Structure
"""

from collections import defaultdict
import re

class Node:
    """Simple node class, linked list to keep forward chain in sequence
    Holds:
        key:        identifies which column this is in, key of dictionary of which this is part of
        sequence:   # separated string of keys that get to this one node
        next        list of nodes this points to and are upstream in sequence
        last        list of nodes this is pointed to, and who are downstream in sequence
    """
    def __init__(self, key, sequence):
        """Single node of forward looking linked list
        Arguments:
            key:        string, should be the key of the dictionary whose list this will be part of
            sequence:   string, # seprated sequence of how we got to this node
        Returns:
            None
        """
        self.key = key
        self.sequence = sequence
        self.nexts = []
        self.lasts = []

    def link_nexts(self, n_next):
        """Link a node as being upstream to this one
        Arguments:
            n_next      Node, this will be added to the current 'next' list
        Returns:
            None
        """
        self.nexts.append(n_next)
        self.nexts = list(set(self.nexts))

    def link_last(self, n_last):
        self.last.append(n_last)

    def __repr__(self):
        return "<node: {},{}>".format(self.key,self.sequence)


class Hydraseq:
    def __init__(self, uuid):
        self.uuid = uuid
        self.columns = defaultdict(list)
        self.n_init = Node('<start>', '<start>')

        self.active = []
        self.predicted = []
        self.sdr_active = []
        self.sdr_predicted = []

    def reset(self):
        """Clear sdrs and reset neuron states to single init active with it's predicts"""
        self.predicted = []
        self.active = []
        self.sdr_predicted = []
        self.sdr_active = []
        self.predicted.extend(self.n_init.nexts)
        self.active.append(self.n_init)
        return self

    def predict(self, str_sentence, is_learning=False):
        """Generate sdr for what comes next in sequence if we know.  Internally set sdr of actives
        Arguments:
            str_sentence:       Either a list of words, or a single space separated sentence
        Returns:
            self                This can be used by calling .sdr_predicted or .sdr_active to get outputs
        """
        words = str_sentence if isinstance(str_sentence, list) else self._get_word_array(str_sentence)
        assert isinstance(words, list), "words must be a list"
        assert isinstance(words[0], list), "{}=>{} is a list of lists and must be non empty".format(str_sentence, words)
        self.reset()

        [self.hit(word, self._hist(words, idx), is_learning) for idx, word in enumerate(words)]

        self.sdr_active    = sorted([node.sequence for node in self.active])
        self.sdr_predicted = sorted(list(set([node.key for node in self.predicted])))

        return self

    def _get_word_array(self, str_sentence):
        return [[word] for word in re.findall(r"[\w'/-:]+|[.,!?;]", str_sentence)]

    def _hist(self, words, idx):
        """Return a # concatenated history up to the current passed index"""
        arr_str_words = [ "-".join(word) for word in words[:(idx+1)] ]
        return "|".join(arr_str_words)

    def hit(self, word, seq_hist, is_learning=True):
        """Process one word in the sequence
        Arguments:
            word        string, current word being processed
            seq_hist    string, represents word history up to how, # separated concatenation
        Returns
            self        so we can chain query for active or predicted
        """
        last_active, last_predicted = self.active[:], self.predicted[:]
        self.active, self.predicted = [], []

        self.active = [node for node in last_predicted if node.key in word]
        self.predicted = list(set([nextn for node in self.active for nextn in node.nexts]))


        if not self.active and is_learning:
            for letter in word:
                node =  Node(letter, seq_hist)
                self.columns[letter].append(node)
                self.active.append(node)

                [n.link_nexts(node) for n in last_active]

        if is_learning: assert self.active
        return self

    def get_sdrs(self):
        return [self.sdr_active, self.sdr_predicted]

    def get_counts(self):
        count = 0
        for lst_nrns in self.columns:
            count += len(lst_nrns)
        return len(self.columns), count + 1

    def __repr__(self):
        return "uuid: {}\nn_init: {}\npredicted: {}\nactive: {}\nsdr_active: {}\nsdr_predicted: {}".format(
            self.uuid,
            self.n_init,
            self.predicted,
            self.active,
            self.sdr_active,
            self.sdr_predicted
        )
