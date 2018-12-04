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
    def __init__(self, uuid, hydraseq=None):
        self.uuid = uuid
        self.n_init = Node('')
        self.active_nodes = []
        self.active_sequences = []
        self.next_nodes = []
        self.next_sequences = []
        self.surprise = False

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
        return [[word] for word in re.findall(r"[\w'/-:]+|[.,!?;]", str_sentence)]

    def get_node_count(self):
        count = 0
        for key, lst_nrns in self.columns.items():
            count += len(lst_nrns)
        return len(self.columns), count + 1

    def self_insert(self, str_sentence):
        """Generate labels for each seuqential sequence. Ex a, ab, abc, abcd..."""
        _, current_count = hds.get_node_count()
        for idx, word in enumerate(sentence):
            if hds.look_ahead(word).surprise:
                hds.insert(" ".join(sentence[:idx])+' _'+str(current_count))
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



#######################################################################################################################
#             NEW THINK STACK!
#######################################################################################################################

Convo = namedtuple('Convo', ['start', 'end', 'pattern', 'lasts', 'nexts'])
endcap = Convo(-1,-1,['end'], [],[])
def to_convo_node(lst_stuff):
    return Convo(lst_stuff[0], lst_stuff[1], lst_stuff[2], [], [])

def link(conv1, conv2):
    conv1.nexts.append(conv2)
    conv2.lasts.append(conv1)

def to_tree_nodes(lst_convos):
    """Convert a list of convolutions, list of [start, end, [words]] to a tree and return the end nodes.
    Args:
        lst_convos, a list of convolutions to link end to end.
    Returns:
        a list of the end ThalaNodes, which if followed in reverse describe valid sequences by linking ends.
    """
    frame = defaultdict(list)
    end_nodes = []
    for convo in lst_convos:
        if frame[convo[0]]:
            for current_node in frame[convo[0]]:
                convo_node = to_convo_node(convo)
                link(current_node, convo_node)
                end_nodes.append(convo_node)
                if current_node in end_nodes: end_nodes.remove(current_node)
                frame[convo_node.end].append(convo_node)
        else:
            convo_node = to_convo_node(convo)
            end_nodes.append(convo_node)
            frame[convo_node.end].append(convo_node)
    return end_nodes

def reconstruct(end_nodes):
    """Take a list of end_nodes and backtrack to construct list of [start, end, [words]]
    Args:
        end_nodes, a list of end point Thalanodes which when followed in reverse create a valid word sequence.
    Returns:
        list of [start, end, [words]] where each is validly linked with start=end
    """
    stack = []
    for node in end_nodes:
        sentence = []
        sentence.append([node.start, node.end, node.pattern])
        while node.lasts:
            node = node.lasts[0]
            sentence.append([node.start, node.end, node.pattern])
        sentence.reverse()
        stack.append(sentence)
    return stack

def patterns_only(sentence):
    """Return a list of the valid [words] to use in a hydra seqeunce
    Args:
        sentence, a list of [start, end, [words]]
    Returns:
        a list of [words], which in effect are a sentence that can be processed by a hydra
    """
    return [sent[2] for sent in sentence]

def get_init_sentence_from_hydra(hd0):
    """Return a list of [start, end, [words]] for initial hydra.
    The hydra should have a uni-word sequence since it represents the input sentence.
    Args:
        hd0, hydra with the simple sentence inserted, encapped with _sentence or any output
    Returns:
        list of [start, end, [word]] for use up the chain of hydras.
    """
    sentence = []
    node = hd0.n_init.nexts[0]
    assert len(hd0.n_init.nexts) == 1
    idx = 0
    while node.nexts:
        sentence.append([idx, idx+1, [node.key]])
        assert len(node.nexts) == 1
        node = node.nexts[0]
        idx+=1
    return [sentence]


def run_them_all(sentences, hydra):
    """Run convolution and get next sentence(s) for each sentence in the list given using this hydra
    Args:
        sentences, a list of sentences, where a sentence is a list of [start, end, [words]]
    Returns:
        a list of next sentences as processed by the given hydra.
    """
    next_sentences = []
    for sent in sentences:
        conv = hydra.convolutions(patterns_only(sent))
        for item in reconstruct(to_tree_nodes(conv)):
            next_sentences.append(item)
    return next_sentences

def think(lst_hydras):
    """Given a list of hydras, where the first hd0 has a simple sentence, propagate up the hydras and return the layer of
    valid sentences.
    Args:
        lst_hydras, a list of hydras.  The first is inserted with only the sentece, the second is encoder, and the rest
            represent higher level sequences
    Return:
        A list of lists of sentences valid per each layer transition between hydras.
    """
    active_layers = []
    for idx, hydra in enumerate(lst_hydras):
        sentences = run_them_all(sentences, hydra) if idx != 0 else get_init_sentence_from_hydra(hydra)
        active_layers.append(sentences)

    return active_layers

#######################################################################################################################
#  REVERSO!
#######################################################################################################################
def get_downwards(hydra, words):
    """Get the words associated with a given output word in a hydra.
    Args:
        hydra, a trained hydra
        downwords, a list of words, whose downward words will be returned.
    Returns:
        a list of words related to the activation of the words given in downwords
    """
    words = words if isinstance(words, list) else hydra.get_word_array(words)
    hydra.reset()
    downs = [w for word in words for node in hydra.columns[word] for w in node.get_sequence().split() if w not in words]

    return sorted(list(set(downs)))

def reverse_convo(hydras, init_word):
    """Take init_word and drive downwards through stack of hydras and return the lowest level valid combination
    Args:
        hydras, a list of trained hydras
    Returns:
        The lowest level list of words that trigger the end word provided (init_word)
    """
    def get_successors(word):
        successors = []
        for hydra in hydras:
            successors.extend(get_downwards(hydra, [word]))
        return successors


    hydras.reverse()
    bottoms = []
    fringe = [init_word]
    dejavu = []
    while fringe:
        word = fringe.pop()
        dejavu.append(word)
        successors = get_successors(word)
        if not successors:
            bottoms.append(word)
        else:
            fringe = fringe + [word for word in successors if word not in dejavu]
            fringe = list(set(fringe))
            print(fringe, " : ", word, " : ", successors)
    return sorted(bottoms)

def run_convolutions(words, seq, nxt="_"):
    words = words if isinstance(words, list) else seq.get_word_array(words)
    hydras = []
    results = []

    for idx, word0 in enumerate(words):
        word_results = []
        hydras.append(Hydraseq(idx, seq))
        for depth, hydra in enumerate(hydras):
            next_hits = [word for word in hydra.hit(word0, is_learning=False).get_next_values() if word.startswith(nxt)]
            if next_hits: word_results.append([depth, idx+1, next_hits])
        results.extend(word_results)
    return results

def get_encoding_only(results):
    """resunt is [left<int>, right<int>, encoding<list<strings>>"""
    return [code[2] for code in results]

def parse(sequemems, sentence):
    for sequemem in sequemems:
        results = run_convolutions(sentence, sequemem, sequemem.uuid)
        sentence = get_encoding_only(results)
        print(results)
    return results
