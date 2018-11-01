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
        if len(self.lasts) > 1:
            past = "(" + "|".join([n_last.get_sequence() for n_last in self.lasts]) + ")"
            return " ".join([past, self.key])
        elif len(self.lasts) == 1:
            past = "|".join([n_last.get_sequence() for n_last in self.lasts])
            return " ".join([past, str(self.key)])
        else:
            return self.key


    def __repr__(self):
        return "<node: {},{}>".format(self.key,self.get_sequence())


class Hydraseq:
    def __init__(self, uuid, hydraseq=None):
        self.uuid = uuid
        self.n_init = Node('(*)')
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
        return sorted([node.key for node in self.active_nodes])

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

    def _hist(self, words, idx):
        """Return a # concatenated history up to the current passed index"""
        arr_str_words = [ "-".join(word) for word in words[:(idx+1)] ]
        return "|".join(arr_str_words)



    def get_node_count(self):
        count = 0
        for lst_nrns in self.columns:
            count += len(lst_nrns)
        return len(self.columns), count + 1

    def __repr__(self):
        return "uuid: {}\nn_init: {}:\nactive values: {}\nnext values: {}".format(
            self.uuid,
            self.n_init,
            self.get_active_values(),
            self.get_next_values()
        )

def run_convolutions(words, seq, debug=False):
    words = words if isinstance(words, list) else seq.get_word_array(words)
    if debug: print(words)
    hydras = []
    results = []

    for idx, word0 in enumerate(words):
        if debug: print(word0)
        word_results = []
        hydras.append(Hydraseq(idx, seq))
        for depth, hydra in enumerate(hydras):
            next_hits = [word for word in hydra.hit(word0, is_learning=False).get_next_values() if word.startswith(seq.uuid)]
            if debug: print(next_hits)
            if next_hits: word_results.append([depth, idx+1, next_hits])
        results.extend(word_results)
    return results

def get_encoding_only(results):
    """result is [left<int>, right<int>, encoding<list<strings>>"""
    return [code[2] for code in results]

def parse(hydras, sentence):
    for hydra in hydras:
        results = run_convolutions(sentence, hydra, hydra.uuid)
        sentence = get_encoding_only(results)
        print(results)
    return results

def generate_tree(lst_nods):
    seq = Hydraseq("_")
    seq.insert("0")

    for idx, nod in enumerate(lst_nods):
        for nd in seq.columns[str(nod[0])]:
            node = Node(nod[2])
            nd.nexts.append(node)
            node.lasts.append(nd)
            seq.columns[str(nod[1])].append(node)
    return seq

def flatten_tree(seq, debug=False):
    print("WTH?")
    sequences = []
    for node in [node for _, lst_nodes in seq.columns.items() for node in lst_nodes if not node.nexts]:
        if debug: print("node.get_sequences(): ", node.get_sequence())
        outcome = " ".join(node.get_sequence().split()[2:])
        if debug: print("outcome: ", outcome)
        found_list = list(eval(outcome.replace("] [", "], [")))
        sequences.append(found_list)
    return sequences

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

def stackem(lst_convos):
    frame = defaultdict(list)
    ends = []
    for convo in lst_convos:
        if frame[convo[0]]:
            for cnode in frame[convo[0]]:
                convo_node = to_convo_node(convo)
                link(cnode, convo_node)
                ends.append(convo_node)
                if cnode in ends: ends.remove(cnode)
                frame[convo_node.end].append(convo_node)
        else:
            convo_node = to_convo_node(convo)
            ends.append(convo_node)
            frame[convo_node.end].append(convo_node)
    return ends

def recon(end_nodes):
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

def pats_only(sentence):
    return [sent[2] for sent in sentence]

def get_init_sentence_from_hydra(hd0):
    sentence = []
    node = hd0.n_init.nexts[0]
    idx = 0
    while node.nexts:
        sentence.append([idx, idx+1, [node.key]])
        node = node.nexts[0]
        idx+=1
    return [sentence]


def run_them_all(sentences, hd1):
    next_sentences = []
    for sent in sentences:
        conv = run_convolutions(pats_only(sent), hd1)
        for item in recon(stackem(conv)):
            next_sentences.append(item)
    return next_sentences

def think(lst_hydras):
    active_layers = []
    for idx, hydra in enumerate(lst_hydras):
        sentences = run_them_all(sentences, hydra) if idx != 0 else get_init_sentence_from_hydra(hydra)
        active_layers.append(sentences)
    return active_layers

#######################################################################################################################
#  REVERSO!
#######################################################################################################################
def get_downwards(seq, downwords):
    seq.reset()
    downs = []
    for downword in downwords:
        for node in seq.columns[downword]:
            downs.extend(node.get_sequence().split()[1:-1])
    return downs

def reverse_convo(stack_seqs, init_word):
    downwords = [init_word]
    for seq in stack_seqs:
        downwords = get_downwards(seq, downwords)
        if not downwords: downwords = [init_word]
    return downwords

#>  hd3.look_ahead("3_face")
def get_downwards(seq, downwords):
    seq.reset()
    downs = []
    for downword in downwords:
        for node in seq.columns[downword]:
            downs.extend(node.get_sequence().split()[1:-1])
    return downs

def reverse_convo(stack_seqs, init_word):
    downwords = [init_word]
    for seq in stack_seqs:
        downwords = get_downwards(seq, downwords)
        if not downwords: downwords = [init_word]
    return downwords

#> reverse_convo([hd3, hd2, hd1], '3_face')
#> ['o', 'o', 'L', 'm']
