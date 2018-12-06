"""
Basic Memory Data Structure
"""

from collections import defaultdict, namedtuple
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
        assert len(self.lasts) <= 1, "Node lasts count should always be 1 or 0"
        past = "|".join([n_last.get_sequence() for n_last in self.lasts])
        return " ".join([past.strip(), str(self.key)]).strip()

    def get_sequence_nodes(self):
        fringe = [self.lasts]
        sequence = []
        while fringe:
            current_list = fringe.pop()
            sequence.insert(0, current_list)
            for node in current_list:
                if node.lasts:
                    fringe.append(node.lasts)
        return sequence[1:]

    def __repr__(self):
        return str(self.key)


class Hydraseq:
    def __init__(self, uuid, hydraseq=None, rex=None):
        self.uuid = uuid
        self.n_init = Node('')
        self.active_nodes = []
        self.active_sequences = []
        self.next_nodes = []
        self.next_sequences = []
        self.surprise = False
        self.rex = rex
        if hydraseq:
            self.columns = hydraseq.columns
            self.n_init.nexts = hydraseq.n_init.nexts
            self.reset()
        else:
            self.columns = defaultdict(list)


    def reset(self):
        """Clear sdrs and reset neuron states to single init active with it's predicts"""
        self.next_nodes = []
        self.active_nodes = []
        self.active_sequences = []
        self.next_nodes.extend(self.n_init.nexts)
        self.active_nodes.append(self.n_init)
        self.surprise = False
        return self


    def get_active_sequences(self):
        return sorted([node.get_sequence() for node in self.active_nodes])

    def get_active_values(self):
        return sorted(list(set([node.key for node in self.active_nodes])))

    def get_next_sequences(self):
        return sorted([node.get_sequence() for node in self.next_nodes])

    def get_next_values(self):
        return sorted(list(set([node.key for node in self.next_nodes])))

    def look_ahead(self, arr_sequence):
        return self.insert(arr_sequence, is_learning=False)

    def insert(self, str_sentence, is_learning=True):
        """Generate sdr for what comes next in sequence if we know.  Internally set sdr of actives
        Arguments:
            str_sentence:       Either a list of words, or a single space separated sentence
        Returns:
            self                This can be used by calling .sdr_predicted or .sdr_active to get outputs
        """
        if not str_sentence: return self
        words = str_sentence if isinstance(str_sentence, list) else self.get_word_array(str_sentence)
        assert isinstance(words, list), "words must be a list"
        assert isinstance(words[0], list), "{}=>{} s.b. a list of lists and must be non empty".format(str_sentence, words)
        self.reset()

        [self.hit(word, is_learning) for idx, word in enumerate(words)]

        return self

    def hit(self, lst_words, is_learning=True):
        """Process one word in the sequence
        Arguments:
            lst_words   list<strings>, current word being processed
        Returns
            self        so we can chain query for active or predicted
        """
        if is_learning: assert len(lst_words) == 1, "lst_words must be singulre if is_learning"
        last_active, last_predicted = self._save_current_state()

        self.active_nodes = self._set_actives_from_last_predicted(last_predicted, lst_words)
        self.next_nodes   = self._set_nexts_from_current_actives(self.active_nodes)

        if not self.active_nodes and is_learning:
            self.surprise = True
            for letter in lst_words:
                node =  Node(letter)
                self.columns[letter].append(node)
                self.active_nodes.append(node)

                [n.link_nexts(node) for n in last_active]
        elif not self.active_nodes:
            self.surprise = True

        if is_learning: assert self.active_nodes
        return self

    def _save_current_state(self):
        return self.active_nodes[:], self.next_nodes[:]
    def _set_actives_from_last_predicted(self, last_predicted, lst_words):
        return [node for node in last_predicted if node.key in lst_words]
    def _set_nexts_from_current_actives(self, active_nodes):
        return list({nextn for node in active_nodes for nextn in node.nexts})

    def get_word_array(self, str_sentence):
        if self.rex:
            return [[word] for word in re.findall(self.rex, str_sentence)]
        else:
            return [[word.strip()] for word in str_sentence.strip().split()]

    def get_node_count(self):
        count = 0
        for key, lst_nrns in self.columns.items():
            count += len(lst_nrns)
        return len(self.columns), count + 1

    def self_insert(self, str_sentence):
        """Generate labels for each seuqential sequence. Ex a, ab, abc, abcd..."""
        if not str_sentence: return self
        words = str_sentence if isinstance(str_sentence, list) else self.get_word_array(str_sentence)
        assert isinstance(words, list), "words must be a list"
        assert isinstance(words[0], list), "{}=>{} s.b. a list of lists and must be non empty".format(str_sentence, words)
        
        _, current_count = self.get_node_count()
        for idx, word in enumerate(words):
            if self.look_ahead([word]).surprise:
                lst_word = words[:idx+1]
                lst_word.extend([['_'+str(current_count)]])
                self.insert(lst_word)
                current_count += 1

    def convolutions(self, words):
        """Run convolution on words using the hydra provided.
        Args:
            words, list<list<strings>>, the words, usually representing a coherent sentence or phrase
            hydra, hydraseq, a trained hydra usually trained on the set of words used in sentence.
            debug, output intermediate steps to console
        Returns:
            a list of convolutions, where each convolution is [start, end, [words]]
        """
        words = words if isinstance(words, list) else self.get_word_array(words)

        hydras = []
        results = []

        for idx, word in enumerate(words):
            word_results = []
            hydras.append(Hydraseq(idx, self))
            for depth, _hydra in enumerate(hydras):
                next_hits = []
                for next_word in _hydra.hit(word, is_learning=False).get_next_values():
                    if next_word.startswith(self.uuid):
                        next_hits.append(next_word)
                if next_hits: word_results.append([depth, idx+1, next_hits])
            results.extend(word_results)
        return results


    def __repr__(self):
        return "Hydra:\n\tactive nodes: {}\n\tnext nodes: {}".format(
            self.active_nodes,
            self.next_nodes
        )

###################################################################################################
# END HYDRA BEGIN CONVOLUTION NETWORK
###################################################################################################
