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
        self.depth = 0

    def link_nexts(self, n_next, d_depths=None):
        """Link a node as being upstream to this one
        Arguments:
            n_next      Node, this will be added to the current 'next' list
        Returns:
            None
        """
        n_next.depth = self.depth + 1

        if d_depths != None: d_depths[n_next.depth] = d_depths[n_next.depth]
        self.nexts.append(n_next)
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
        self.active_nodes = set()
        self.active_sequences = set()
        self.last_active_nodes = set()
        self.last_active_sequences = set()
        self.next_nodes = set()
        self.next_sequences = set()
        self.surprise = False
        self.rex = rex
        self.d_depths = defaultdict(set)
        if hydraseq:
            self.columns = hydraseq.columns
            self.n_init.nexts = hydraseq.n_init.nexts
            self.path_nodes = hydraseq.path_nodes
            self.active_synapses = hydraseq.active_synapses
            self.reset()
        else:
            self.columns = defaultdict(set)
            self.path_nodes = set()
            self.active_synapses = {}

    def set_active_synapses(self, out_words):
        """Set a list of words to be used as a filter to active columns.  Used to simulate expected
            columns in a context
        Args:
            out_words, list<strings>, each string is a word in output layer.  The downward words that are part
                           triggering it are collected in a set and used as filter.
                           For example, 2_FACE might be triggered by 1_EYES, 1_NOSE, 1_MOUTH, which would
                           consitute the words used as filter so we ignore things like 1_ARM.
        Return:
            list<string>, a list of the downward words that may trigger the words in out_words, these are also
                          set in self.active_synapses
        """
        assert isinstance(out_words, list), "out_words must be a list"
        if not out_words: return [] # [] will be ignored and hydra will behave as normal
        assert isinstance(out_words[0], str), "out_words must be list<str> but is {}".format(out_words)
        self.active_synapses = self.get_downwards(out_words)
        return self.active_synapses[:]

    def reset_active_synapses(self):
        """Restore the active_synapse variable to an empty set.  Operate as normal"""
        self.active_synapses = {}
        return self

    def reset(self):
        """Clear sdrs and reset neuron states to single init active with it's predicts"""
        self.next_nodes = set()
        self.active_nodes = set()
        self.active_sequences = []
        self.last_active_nodes = set()
        self.last_active_sequences = set()
        self.next_nodes.update(self.n_init.nexts)
        self.active_nodes.add(self.n_init)
        self.surprise = False
        return self

    def load_from_file(self, fpath):
        with open(fpath, 'r') as source:
            for line in source:
                self.insert(self.get_word_array(line))
        return self

    def get_active_sequences(self):
        return sorted([node.get_sequence() for node in self.active_nodes])

    def get_active_values(self):
        return sorted({node.key for node in self.active_nodes})

    def get_last_active_sequences(self):
        return sorted([node.get_sequence() for node in self.last_active_nodes])

    def get_last_active_values(self):
        return sorted({node.key for node in self.last_active_nodes})

    def get_next_sequences(self):
        return sorted([node.get_sequence() for node in self.next_nodes])

    def get_next_values(self):
        return sorted({node.key for node in self.next_nodes})

    def forward_prediction(self):
        """Starting from current predicted, roll forward and return list of end nodes"""
        fringe = list(self.next_nodes)
        ends = []
        while fringe:
            node = fringe.pop()
            if node.nexts:
                fringe.extend(node.nexts)
            else:
                ends.append(node)
        return ends

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
        if not words: return self
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
        if is_learning: assert len(lst_words) == 1, "lst_words must be singular if is_learning"
        lst_words = [word for word in lst_words if word in self.active_synapses] if self.active_synapses else lst_words
        last_active, last_predicted = self._save_current_state()

        self.active_nodes = self._set_actives_from_last_predicted(last_predicted, lst_words)
        if self.path_nodes: self.active_nodes = self.active_nodes.intersection(self.path_nodes)

        self.next_nodes   = self._set_nexts_from_current_actives(self.active_nodes)
        if self.path_nodes: self.next_nodes = self.next_nodes.intersection(self.path_nodes)

        if not self.active_nodes and is_learning:
            self.surprise = True
            for letter in lst_words:
                node =  Node(letter)
                self.columns[letter].add(node)
                self.active_nodes.add(node)

                [n.link_nexts(node, self.d_depths) for n in last_active]
        elif not self.active_nodes:
            self.surprise = True

        if is_learning: assert self.active_nodes
        return self

    def _save_current_state(self):
        self.last_active_nodes = self.active_nodes.copy()
        self.last_active_sequences = self.active_sequences.copy()
        return self.active_nodes.copy(), self.next_nodes.copy()

    def _set_actives_from_last_predicted(self, last_predicted, lst_words):
        return {node for node in last_predicted if node.key in lst_words}
    def _set_nexts_from_current_actives(self, active_nodes):
        return {nextn for node in active_nodes for nextn in node.nexts}

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

    def full_insert(self, sent):
        words = sent.split()
        for idx in range(len(words)):
            self.self_insert(" ".join(words[idx:-1]))

    def convo_as_json(self, lst_convo, words):
        (start, end, convo) = lst_convo
        return {
            'words': words[start:end],
            'start': start,
            'end': end,
            'convo': convo
        }

    def convolutions(self, words, as_json=True):
        """Run convolution on words using the hydra provided.
        Args:
            words, list<list<strings>>, the words, usually representing a coherent sentence or phrase
            hydra, hydraseq, a trained hydra usually trained on the set of words used in sentence.
            debug, output intermediate steps to console
        Returns:
            a list of convolutions, where each convolution is [start, end, [words]]
        """
        assert isinstance(as_json, bool), "as_json should be a bool value"
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
        if as_json:
            return [self.convo_as_json(convo, words) for convo in results]
        else:
            return results

    def get_downwards(self, words):
        """Get the words associated with a given output word in a hydra.
        Args:
            downwords, a list of words, whose downward words will be returned.
        Returns:
            a list of words related to the activation of the words given in downwords
        """
        words = words if isinstance(words, list) else self.get_word_array(words)
        assert isinstance(words, list)
        assert isinstance(words[0], str), "words should be list<str> but is {}".format(words)
        #self.reset()
        downs = {w for word in words for node in self.columns[word] for w in node.get_sequence().split() if w not in words}

        return sorted(downs)


    def activate_node_pathway(self, top_words):
        """Create a set of references to the nodes used in the input layer to activate the top words.
            This includes all paths.  For example, if 2_EFRAIN triggers via 1_E 1_ F R A I N and O L I V, then
            the return set will include both sets of letters.  This set can then be used to dot product
            and weed out any paths that are not congruent.
        """
        if not top_words: return []
        top_words = top_words.split() if isinstance(top_words, str) else top_words
        assert isinstance(top_words, list), "top_words is a list"
        assert isinstance(top_words[0], str), "elements of top_words must be strings"

        top_nodes = [node for word in top_words for node in self.columns[word]]

        self.path_nodes = {path_node for node in top_nodes for path_nodes in node.get_sequence_nodes() for path_node in path_nodes}
        for node in top_nodes:
            self.path_nodes.add(node)
        return self.get_downwards(top_words)

    def reset_node_pathway(self):
        self.path_nodes = {}
        return self



    def __repr__(self):
        return "Hydra:\n\tactive nodes: {}\n\tnext nodes: {}".format(
            self.active_nodes,
            self.next_nodes
        )

###################################################################################################
# END HYDRA BEGIN CONVOLUTION NETWORK
###################################################################################################
