"""
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
    def __init__(self, key):
        """Single node of forward looking linked list
        Arguments:
            key:        string, should be the key of the dictionary whose list this will be part of
            sequence:   string, # seprated sequence of how we got to this node
        Returns:
            None
        """
        self.key = key
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
        n_next.link_last(self)

    def link_last(self, n_last):
        self.lasts.append(n_last)

    def get_sequence(self):
        if len(self.lasts) > 1:
            past = "(" + "|".join([n_last.get_sequence() for n_last in self.lasts]) + ")"
            return ">".join([past, self.key])
        elif len(self.lasts) == 1:
            past = "|".join([n_last.get_sequence() for n_last in self.lasts])
            return ">".join([past, self.key])
        else:
            return self.key


    def __repr__(self):
        return "<node: {},{}>".format(self.key,self.get_sequence())


class Hydraseq:
    def __init__(self, uuid):
        self.uuid = uuid
        self.columns = defaultdict(list)
        self.n_init = Node('(*)')

        self.active_nodes = []
        self.active_sequences = []
        self.active_values = []
        self.next_nodes = []
        self.next_sequences = []
        self.next_values = []

    def reset(self):
        """Clear sdrs and reset neuron states to single init active with it's predicts"""
        self.next_nodes = []
        self.active_nodes = []
        self.next_values = []
        self.active_sequences = []
        self.next_nodes.extend(self.n_init.nexts)
        self.active_nodes.append(self.n_init)
        return self


    def get_active_sequences(self):
        return sorted([node.get_sequence() for node in self.active_nodes])

    def get_active_values(self):
        return sorted([node.key for node in self.active_nodes])

    def get_next_sequences(self):
        return sorted([node.get_sequence() for node in self.next_nodes])

    def get_next_values(self):
        return sorted(list(set([node.key for node in self.next_nodes])))

    def insert(self, str_sentence, is_learning=True):
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

        return self

    def look_ahead(self, arr_sequence):
        return self.insert(arr_sequence, is_learning=False)

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
        last_active, last_predicted = self.active_nodes[:], self.next_nodes[:]
        self.active_nodes, self.next_nodes = [], []

        self.active_nodes = [node for node in last_predicted if node.key in word]
        self.next_nodes = list(set([nextn for node in self.active_nodes for nextn in node.nexts]))


        if not self.active_nodes and is_learning:
            for letter in word:
                node =  Node(letter)
                self.columns[letter].append(node)
                self.active_nodes.append(node)

                [n.link_nexts(node) for n in last_active]

        if is_learning: assert self.active_nodes
        return self



    def get_node_count(self):
        count = 0
        for lst_nrns in self.columns:
            count += len(lst_nrns)
        return len(self.columns), count + 1

    def __repr__(self):
        return "uuid: {}\nn_init: {}:\nactive values: {}\nnext values: {}".format(
            self.uuid,
            self.n_init,
            self.active_values,
            self.next_values
        )
