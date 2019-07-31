from hydraseq.minicolumn import MiniColumn



sentence = "spring leaves spring"
source_files = ["seasons.0.txt", "seasons.1.txt", "seasons.2.txt"]
mcol = MiniColumn(source_files, "tests/data")
assert isinstance(mcol, MiniColumn)

ctree = mcol.compute_convolution_tree(sentence)
# assert ctree == []
objtree = mcol.objectize_convolution_tree(ctree)

print("top convos: ",objtree.convos)

class Node:
    def __init__(self, convos=[]):
        self.convos = convos
        self.nexts = []
        self.lasts = []

    def show(self):
        print("Convos:")
        for convo in self.convos:
            print("    ", convo)
        print("Nexts:")
        for nnext in self.nexts:
            print(nnext)
        print("Lasts:")
        for last in self.lasts:
            print(last)

def create_ntree(ctree):
    head_node = Node(convos=ctree[0])
    fringe = [ctree[1]]
    current_node = head_node
    for node in fringe:
        n = Node(convos=node[0])
        current_node.nexts.append(n)
        n.lasts.append(current_node)
    return head_node

def process_tp_node(tp_node):
    """in comes a two lister, returns the new node"""
    node = Node(tp_node[0])
    if len(tp_node) == 2:
        for ns in tp_node[1]:
            node.nexts.append(process_tp_node(ns[0]))

    return node

otree = process_tp_node(ctree)
