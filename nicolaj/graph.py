from collections import namedtuple


class MyDirection:
    North = (0, 1)
    East = (1, 0)
    West = (-1, 0)
    South = (0, -1)
    Stop = (0, 0)

    opposite = {
        North: South,
        East: West,
        West: South,
        South: North,
        Stop: Stop,
    }

    fromStr = {
        'North': North,
        'East': East,
        'West': West,
        'South': South,
        'Stop': Stop,
    }

    toStr = {
        North: 'North',
        East: 'East',
        West: 'West',
        South: 'South',
        Stop: 'Stop',
    }


Node = namedtuple('Node', ['id', 'x', 'y', 'edges'])
Edge = namedtuple('Edge', ['i', 'j', 'weight'])


class Graph(namedtuple('Graph', ['nodes', 'edges'])):

    def add_node(self, x, y) -> Node:
        n = Node(len(self.nodes), x, y, [])
        self.nodes.append(n)
        return n

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
            s += f'  {n.id} at ({n.x} {n.y})\n'
        s += f'Edges ({len(self.edges)}):\n'
        for e in self.edges:
            s += f'  {e.i}--{e.j} weight {e.weight}\n'
        return s[:-1]
