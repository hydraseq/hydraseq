"""
class MiniColumn: A stack of hydraseqs for hyrarchical convolutions
    def __init__(self, source_files=[], dir_root='.'):
    def reset(self):
    def compute_convolution_tree(self, sentence):
    def resolve_convolution(self, convos):
    def get_state(self):
    def to_tree_nodes(self, lst_convos):
    def reconstruct(self, end_nodes):
    def to_convo_node(self, lst_stuff):
    def link(self, conv1, conv2):
    def patterns_only(self, convos):
    def reverse_convo(self, init_word):
"""
from hydraseq import Hydraseq
import hydraseq
from collections import defaultdict, namedtuple
import re

Convo = namedtuple('Convo', ['start', 'end', 'pattern', 'lasts', 'nexts'])
endcap = Convo(-1,-1,['end'], [],[])

class MiniColumn:
    """A stack of trained hydras which can get layers of convolutions
    Initialize this with a set of training files, one per hydra.
    """
    def __init__(self, source_files=[], dir_root='.'):
        """Initialize hydras from files.
        Args
            source_files: list<str> a list of filenames with name formated in triplets.
                                filename.uuid.ext, uuid should be the internal end marker
            dir_root: str, a directory base if the files are not located in script dir
        Returns
            None
        """
        self.base_hydra = hydraseq.Hydraseq('_')
        self.hydras = []
        for fname in source_files:
            base, uuid, ext = fname.split('.')
            h = hydraseq.Hydraseq(uuid+'_')
            with open("{}/{}".format(dir_root, fname), 'r') as source:
                for line in source:
                    h.insert(line.strip())
            self.hydras.append(h)
        self.depth = len(self.hydras)
        self.convolutions = []

    def reset(self):  # returns self
        """reset all hydras, and set convolutions, active and predicted arrays to empty"""
        [hydra.reset() for hydra in self.hydras]
        self.convolutions = []
        self.active = []
        self.predicted = []
        return self

    def compute_convolution_tree(self, sentence): # -> list of convo paths
        """Generate the stack of convolutions using this sentence
        Internally calculates the convolution and saves them in self.convolutions.
        Each convolution is then forward fed to the next hydra.

        Args:
            sentence: str, A sentence in plain separated words
        Returns:
           list of convo paths
        convos: A list of all unique atomic unit possible
        convo_path: A list of SEQUENTIAL atomic units filling out a path
        """
        def get_successors(convo_path, hydra):
            self.reset()
            convos = hydra.convolutions(self.patterns_only(convo_path))
            convo_paths = self.resolve_convolution(convos)
            return convo_paths

        head_node = self.resolve_convolution(self.hydras[0].convolutions(sentence))[0]

        successors = get_successors(head_node, self.hydras[1])
        head_node.append(successors)

        for node in successors:
            subsucc = get_successors(node, self.hydras[2])
            node.append(subsucc)

        return head_node

    def compute_convolution_tree_obj(self, sentence): # -> list of convo paths
        """Generate the stack of convolutions using this sentence
        Internally calculates the convolution and saves them in self.convolutions.
        Each convolution is then forward fed to the next hydra.

        Args:
            sentence: str, A sentence in plain separated words
        Returns:
           list of convo paths
        convos: A list of all unique atomic unit possible
        convo_path: A list of SEQUENTIAL atomic units filling out a path
        """
        def get_successors(convo_path, hydra):
            self.reset()
            convos = hydra.convolutions(self.patterns_only_obj(convo_path), as_json=True)
            convo_paths = self.resolve_convolution_obj(convos)
            return convo_paths

        head_node = self.resolve_convolution_obj(self.hydras[0].convolutions(sentence, as_json=True))[0]
        #print("HEAD_NODE: ",head_node)
        successors = get_successors(head_node, self.hydras[1])
        head_node.append(successors)

        for node in successors:
            subsucc = get_successors(node, self.hydras[2])
            node.append(subsucc)

        return head_node

    def resolve_convolution(self, convos): # list of possible thru paths
        """Take a set of convolutions, and return a list of end to end possible paths"""
        return self.reconstruct(self.to_tree_nodes(convos))

    def resolve_convolution_obj(self, convos): # list of possible thru paths
        """Take a set of convolutions, and return a list of end to end possible paths"""
        return self.reconstruct_obj(self.to_tree_nodes_obj(convos))

    def get_state(self):
        """Return the states of the internal hydras
        Args:
            None
        Returns:
            list<list<active nodes>, list<next nodes>>
        """
        self.active = []
        self.predicted = []
        for hydra in self.hydras:
            self.active.append(hydra.active_nodes)
            self.predicted.append(hydra.next_nodes)
        return [self.active, self.predicted]

    def to_tree_nodes(self, lst_convos): # -> list of thalanodes
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
                    convo_node = self.to_convo_node(convo)
                    self.link(current_node, convo_node)
                    end_nodes.append(convo_node)
                    if current_node in end_nodes: end_nodes.remove(current_node)
                    frame[convo_node.end].append(convo_node)
            else:
                convo_node = self.to_convo_node(convo)
                end_nodes.append(convo_node)
                frame[convo_node.end].append(convo_node)
        return end_nodes

    def to_convo_node_obj(self, convo_obj):
        return {
            'word': convo_obj['word'],
            'convo': convo_obj['convo'],
            'start': convo_obj['start'],
            'end': convo_obj['end'],
            'lasts': [],
            'nexts': []
        }

    def to_tree_nodes_obj(self, lst_convos_obj): # -> list of thalanodes
        """Convert a list of convolutions, list of [start, end, [words]] to a tree and return the end nodes.
        Args:
            lst_convos, a list of convolutions to link end to end.
        Returns:
            a list of the end ThalaNodes, which if followed in reverse describe valid sequences by linking ends.
        """
        frame = defaultdict(list)
        end_nodes = []
        for convo in lst_convos_obj:
            if frame[convo['start']]:
                for current_node in frame[convo['start']]:
                    convo_node = self.to_convo_node_obj(convo)
                    self.link_obj(current_node, convo_node)
                    end_nodes.append(convo_node)
                    if current_node in end_nodes: end_nodes.remove(current_node)
                    frame[convo_node['end']].append(convo_node)
            else:
                convo_node = self.to_convo_node_obj(convo)
                end_nodes.append(convo_node)
                frame[convo_node['end']].append(convo_node)
        return end_nodes


    def reconstruct(self, end_nodes):
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

    def reconstruct_obj(self, end_nodes_objs):
        """Take a list of end_nodes and backtrack to construct list of [start, end, [words]]
        Args:
            end_nodes, a list of end point Thalanodes which when followed in reverse create a valid word sequence.
        Returns:
            list of [start, end, [words]] where each is validly linked with start=end
        """
        stack = []
        for node in end_nodes_objs:
            sentence = []
            tmp_node = node.copy()
            tmp_node.pop('lasts', None)
            sentence.append(tmp_node)
            while node['lasts']:
                node = node['lasts'][0]
                tnode = node.copy()
                tnode.pop('lasts',None)
                sentence.append(tnode)
            sentence.reverse()
            stack.append(sentence)
        return stack

    def to_convo_node(self, lst_stuff):
        return Convo(lst_stuff[0], lst_stuff[1], lst_stuff[2], [], [])

    def link(self, conv1, conv2):
        conv1.nexts.append(conv2)
        conv2.lasts.append(conv1)
    def link_obj(self, obj1, obj2):
        #obj1['nexts'].append(obj2)
        obj2['lasts'].append(obj1)


    def patterns_only(self, convos):
        """Return a list of the valid [words] to use in a hydra seqeunce
        Args:
            sentence, a list of [start, end, [words]]
        Returns:
            a list of [words], which in effect are a sentence that can be processed by a hydra
        """
        return [convo[2] for convo in convos]

    def patterns_only_obj(self, convos):
        """Return a list of the valid [words] to use in a hydra seqeunce
        Args:
            sentence, a list of [start, end, [words]]
        Returns:
            a list of [words], which in effect are a sentence that can be processed by a hydra
        """
        # print("KONVOS", convos)
        # print("ONE KONVO: ", convos[0])
        # print("ONE KONVO CONVO: ", convos[0]['convo'])
        return [convo['convo'] for convo in convos]

    def reverse_convo(self, init_word):
        """Take init_word and drive downwards through stack of hydras and return the lowest level valid combination
        Args:
            hydras, a list of trained hydras
        Returns:
            The lowest level list of words that trigger the end word provided (init_word)
        """
        def get_successors(word):
            successors = []
            for hydra in self.hydras:
                successors.extend(hydra.get_downwards([word]))
            return successors


        self.hydras.reverse()
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
        return sorted(bottoms)

######################################################################################
# END MiniColumn ^^
######################################################################################