"""
Basic Memory Data Structure
"""

from collections import defaultdict, namedtuple
import re

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
