from typing import Tuple, Iterator, List

import game
from layout import Layout
from nicolaj.graph import Graph, Node, MyDirection


class StaticInfo:
    def __init__(self, layout: Layout):
        self.layout = layout
        self.graph = Graph([], [])
        self.graph_lut = {}
        self.start_node: Node = None
        self.build_graph()

        # self.heuristic = Heuristic(self.graph)
        # all_but_init_visited = tuple(
        #     [False] + [True for _ in range(1, len(self.graph.nodes))] + [e.weight > 1 for e in self.graph.edges]
        # )
        # print('Cost of visiting all cells from init:', self.heuristic.smart_cost[(self.start_node.id, all_but_init_visited)])

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

    def get_all_legal_actions(self, position: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
        x, y = position
        for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South, (0, 0)]:
            if not self.layout.walls[x + dx][y + dy]:
                yield dx, dy

    def get_ghost_legal_actions(self, position: Tuple[int, int], direction: Tuple[int, int]) -> List[Tuple[int, int]]:
        actions = []
        x, y = position
        for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South]:
            if not self.layout.walls[x + dx][y + dy]:
                actions.append((dx, dy))
        if len(actions) > 1 and MyDirection.opposite[direction] in actions:
            actions.remove(MyDirection.opposite[direction])
        elif len(actions) == 0:
            actions.append((0, 0))
        return actions
