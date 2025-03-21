
class Edge:
    def __init__(self, i, j, weight):
        self.i = i
        self.j = j
        self.weight = weight


class Node:
    def __init__(self, index, x, y):
        self.index = index
        self.x = x
        self.y = y
        self.edges = []

    def __lt__(self, other):
        return self.index < other.index


class Graph:

    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(self, x, y) -> Node:
        n = Node(len(self.nodes), x, y)
        self.nodes.append(n)
        return n

    def remove_node(self, i):
        for e in self.nodes[i].edges:
            if e.i != i:
                self.nodes[e.i].edges.remove(e)
            if e.j != i:
                self.nodes[e.j].edges.remove(e)
            self.edges.remove(e)
        for e in self.edges:
            if e.i > i:
                e.i -= 1
            if e.j > i:
                e.j -= 1

        del self.nodes[i]
        for j, n in enumerate(self.nodes):
            n.index = j

    def add_edge(self, i, j, weight) -> Edge:
        if j < i:
            i, j = j, i
        e = Edge(i, j, weight)
        self.nodes[i].edges.append(e)
        self.nodes[j].edges.append(e)
        self.edges.append(e)
        return e

    def pretty_str(self):
        s = f'Nodes ({len(self.nodes)}):\n'
        for n in self.nodes:
            s += f'  {n.index} at ({n.x} {n.y})\n'
        s += f'Edges ({len(self.edges)}):\n'
        for e in self.edges:
            s += f'  {e.i}--{e.j} weight {e.weight}\n'
        return s[:-1]
