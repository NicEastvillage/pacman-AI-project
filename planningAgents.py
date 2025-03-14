import time
from collections import namedtuple
from typing import Tuple, List, Dict

import heapq

import numpy as np
from numba import jit

import game
from layout import Layout
from pacman import Directions
from pacman import GameState


class MyDirection:
    North = (0, 1)
    East = (1, 0)
    West = (-1, 0)
    South = (0, -1)

    opposite = {
        North: South,
        East: West,
        West: South,
        South: North,
    }


def tuple_replace[T](tup: Tuple[T, ...], ix: int, val: T) -> Tuple[T, ...]:
    return tup[:ix] + (val,) + tup[ix+1:]


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


class Heuristic:
    def __init__(self, graph: Graph):
        # A mapping from a start node id (pacman current pos) and a list of fully unvisited
        # graph elements (nodes + edges) to the cost of visiting all unvisited nodes and edges
        # from the start node according to Djikstras algorithm
        self.smart_cost: Dict[Tuple[int, Tuple[bool, ...]]] = {}
        self.build_smart_cost_djikstra(graph)

    def get(self, rstate):
        return 0

    def build_smart_cost_djikstra(self, graph):
        print('Using Djikstra to prepare heuristic..', end='')
        node_count = len(graph.nodes)
        el_count = node_count + len(graph.edges)

        all_visitied = tuple([False] * el_count)
        queue = []
        passed = set()

        # Queue "start" states
        for n in graph.nodes:
            heapq.heappush(queue, (0, (n.id, all_visitied)))
            self.smart_cost[(n.id, all_visitied)] = 0

        debug_prev_cost = -1
        while queue:
            cur_cost, cur = heapq.heappop(queue)
            if cur in passed:
                continue
            passed.add(cur)


            if cur_cost > debug_prev_cost:
                print(str(cur_cost) + '..', end='')
                debug_prev_cost = cur_cost

            for succ, w in _successor(graph, cur):
                if succ[1][0]:
                    continue  # Node 0 is always false. It is the start node
                if succ not in passed:
                    succ_cost_by_cur = cur_cost + w
                    if succ_cost_by_cur < self.smart_cost.get(succ, float('inf')):
                        self.smart_cost[succ] = succ_cost_by_cur
                        heapq.heappush(queue, (succ_cost_by_cur, succ))
        print('')


def _successor(graph: Graph, dn: Tuple[int, Tuple[bool, ...]]) -> List[Tuple[Tuple[int, Tuple[bool, ...]], int]]:
    node_count = len(graph.nodes)
    nid, has_food = dn
    initial = not np.array(has_food).any()
    for i, edge in enumerate(graph.edges):
        if has_food[node_count + i]:
            continue  # We could not have come from this edge, it has food
        if not (edge.i == nid or edge.j == nid):
            continue  # This edge does not end at our current node

        new_node = edge.j if edge.i == nid else edge.i

        if has_food[new_node]:
            # We could not have come from this node, it has food.
            # But we might want to do the edge and then turn around.
            if edge.weight <= 1:
                # This edge is too short to have food on it
                continue

            # Only edge had food (if initial, then cost -1 here since last step to the node is unnecessary)
            has_food_edge = tuple_replace(has_food, node_count + i, True)
            w = 2 * edge.weight - 2
            yield (nid, has_food_edge), w

            continue

        if not initial:
            # Neither node or edge had food
            yield (new_node, has_food), edge.weight

        # Only node
        if new_node != nid:
            has_food_node = tuple_replace(has_food, nid, True)
            yield (new_node, has_food_node), edge.weight

        if edge.weight <= 1:
            # This edge is too short to have food on it
            continue

        # Both node and edge had food
        has_food_both = tuple_replace(tuple_replace(has_food, nid, True), node_count + i, True)
        yield (new_node, has_food_both), edge.weight

        # Only edge had food (if initial, then cost -1 here since last step to the node is unnecessary)
        has_food_edge = tuple_replace(has_food, node_count + i, True)
        w = edge.weight - 1 if initial else edge.weight
        yield (new_node, has_food_edge), w


class StaticInfo:
    def __init__(self, layout: Layout):
        self.layout = layout
        self.graph = Graph([], [])
        self.graph_lut = {}
        self.start_node: Node = None
        self.build_graph()
        self.heuristic = Heuristic(self.graph)

        all_but_init_visited = tuple(
            [False] + [True for _ in range(1, len(self.graph.nodes))] + [e.weight > 1 for e in self.graph.edges]
        )
        print('Cost of visiting all cells from init:', self.heuristic.smart_cost[(self.start_node.id, all_but_init_visited)])

    def build_graph(self):
        """
        Turn a layout like this

        %%%%%%%%
        %P   %.%
        %.% . .%
        % % %%%%
        %.  . .%
        % % %G %
        %%%%%%%%

        into a graph like this

         0─0┐ 0
         | 00─┘
         | |
         0─0─0┐
         0 0 └┘

        """

        print("Building graph and LUT...")

        start_x, start_y = (0, 0)
        for isPacman, (x, y) in self.layout.agentPositions:
            if isPacman:
                start_x, start_y = x, y

        walls = self.layout.walls
        marked = game.Grid(self.layout.width, self.layout.height, False)

        def build_rec(x: int, y: int, dist: int, move_dir: Tuple[int, int], from_node: Node):
            assert not marked[x][y]
            assert not walls[x][y]
            marked[x][y] = True
            num_doors = 0
            for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South]:
                if not walls[x + dx][y + dy]:
                    num_doors += 1

            caller_edge = None
            is_intersection = num_doors != 2

            if is_intersection:
                # New intersection
                new_node = self.graph.add_node(x, y)
                caller_edge = self.graph.add_edge(from_node.id, new_node.id, dist)
                self.graph_lut[(x, y)] = (True, new_node)

                dist = 0
                from_node = new_node

            # Move on to relevant neighbors
            for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South]:
                if move_dir == (-dx, -dy):
                    continue  # Do not move backwards

                nx, ny = x + dx, y + dy

                if walls[nx][ny]:
                    continue  # Do not move into walls

                if marked[nx][ny]:
                    # We have seen this neighbor before. It must be in the lut
                    is_node, node = self.graph_lut[(nx, ny)]
                    if is_node:
                        e = self.graph.add_edge(from_node.id, node.id, dist + 1)
                    else:
                        assert is_intersection  # This node have a self-loop
                else:
                    # Undiscovered corridor or intersection ahead
                    e = build_rec(nx, ny, dist + 1, (dx, dy), from_node)

                if not is_intersection:
                    # We are in a corridor, and we now know the edge
                    self.graph_lut[(x, y)] = (False, e)
                    # Our caller is also part of this edge
                    return e

            assert caller_edge is not None
            return caller_edge

        marked[start_x][start_y] = True
        self.start_node = self.graph.add_node(start_x, start_y)
        self.graph_lut[(start_x, start_y)] = (True, self.start_node)

        for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South]:
            nx, ny = start_x + dx, start_y + dy
            if walls[nx][ny]:
                continue  # Do not move into walls

            if marked[nx][ny]:
                # We have seen this neighbor before. It must be in the lut
                is_node, node = self.graph_lut[(nx, ny)]
                if is_node:
                    self.graph.add_edge(self.start_node.id, node.id, 1)
            else:
                # Undiscovered corridor or intersection ahead
                build_rec(nx, ny, 1, (dx, dy), self.start_node)

        print(self.graph.pretty_str())

        s = 'LUT:\n'
        for y in reversed(range(self.layout.height)):
            for x in range(self.layout.width):
                if (x, y) in self.graph_lut:
                    is_node, el = self.graph_lut[(x, y)]
                    s += str(el.id) if is_node else '+'
                else:
                    s += ' '
            s += '\n'
        print(s)


class PolicyRefiner:

    def __init__(self, static_info: StaticInfo):
        self.static_info = static_info
        self.root_state = GameState().initialize(static_info.layout)

    def refine(self):
        pass

    def get_action(self, state: GameState):
        return Directions.STOP


class PlanningAgent(game.Agent):

    def __init__(self, layout: Layout, **kwargs):
        super().__init__(**kwargs)
        self.layout: Layout = layout
        self.static_info: StaticInfo = StaticInfo(layout)
        self.policy = PolicyRefiner(self.static_info)
        self.offline_planning()

    def offline_planning(self):
        # Time limit: 10 minutes

        print("Refining policy...")
        stop_at = time.time() + 9.50  # TODO: Extend to 10 min
        while time.time() < stop_at:
            self.policy.refine()

    def getAction(self, state : GameState):
        # Time limit: approx 1 second
        stop_at = time.time() + 0.95

        self.policy.root_state = state
        while time.time() < stop_at:
            # Some extra refinement
            self.policy.refine()

        return self.policy.get_action(state)
