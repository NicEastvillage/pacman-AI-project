import heapq
from typing import Tuple, Dict

import game
from nicolaj.graph import Graph
from nicolaj.my_state import MyGameState


def approach1(x: float) -> float:
    return x / (x + 1.0)


class Distances:
    BIG_NUMBER = 9999999

    def __init__(self, walls: game.Grid):
        self.walls = walls
        self.cache = [[[[self.BIG_NUMBER for _ in range(walls.height)] for _ in range(walls.width)]
                       for _ in range(walls.height)] for _ in range(walls.width)]

    def get(self, source: Tuple[int, int], destination: Tuple[int, int]):
        if source == destination:
            return 0
        if source > destination:
            source, destination = destination, source

        cached = self.cache[source[0]][source[1]][destination[0]][destination[1]]
        if cached < self.BIG_NUMBER:
            return cached

        # Djikstra's algorithm

        width, height = self.walls.width, self.walls.height
        start_x, start_y = source
        end_x, end_y = destination

        assert not self.walls[start_x][start_y] and not self.walls[end_x][end_y]

        queue = [(0, start_x, start_y)]  # (cost, x, y) - not a priority queue since all edge have cost 1
        visited = set()

        while queue:
            cost, x, y = queue.pop(0)

            if (x, y) in visited:
                continue
            visited.add((x, y))

            if (x, y) == (end_x, end_y):
                self.cache[start_x][start_y][destination[0]][destination[1]] = cost
                return cost

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and not self.walls[nx][ny]:
                    queue.append((cost + 1, nx, ny))

        assert False


class Heuristic:
    def __init__(self, distances: Distances):
        self.distances = distances
        # Key: pacman pos + food grid + loss, value: heuristic
        self.heuristic_cache: Dict[Tuple[Tuple[int, int], game.Grid, bool], float] = {}
        # Key: food grid, value: MST graph + size
        self.mst_cache: Dict[game.Grid, Tuple[Graph, int]] = {}

    def get(self, state: MyGameState, pred: MyGameState | None) -> float:
        loss = state.is_loss()
        cached = self.heuristic_cache.get((state.pacman, state.food, loss))
        if cached:
            return cached
        if loss:
            self.heuristic_cache[(state.pacman, state.food, True)] = 9999999
            return 9999999
        if state.is_win():
            self.heuristic_cache[(state.pacman, state.food, False)] = 0
            return 0

        cached_graph_and_cost = self.mst_cache.get(state.food)
        if cached_graph_and_cost:
            mst_cost = cached_graph_and_cost[1]
        elif pred is None or self.mst_cache.get(pred.food) is None:
            mst_cost = self._mst_prim(state.food)
        else:
            mst_cost = self._mst_by_diff(state, pred)

        dist = dist_to_closest_food(self.distances, state.pacman, state.food)
        cost = mst_cost + approach1(dist)
        self.heuristic_cache[(state.pacman, state.food, False)] = cost
        return cost

    def _mst_prim(self, food: game.Grid) -> int:
        # Prim's algorithm
        graph = Graph()
        for x in range(food.width):
            for y in range(food.height):
                if food[x][y]:
                    graph.add_node(x, y)

        mst_cost = 0
        visited = set()
        pq = [(0, graph.nodes[0], None)]  # (cost, node, anchor node)

        while pq and len(visited) < len(graph.nodes):
            cost, node, anchor = heapq.heappop(pq)

            if (node.x, node.y) in visited:
                continue
            visited.add((node.x, node.y))
            mst_cost += cost
            if anchor is not None:
                graph.add_edge(node.index, anchor.index, cost)

            for other in graph.nodes:
                if (other.x, other.y) not in visited:
                    d = self.distances.get((node.x, node.y), (other.x, other.y))
                    heapq.heappush(pq, (d, other, node))

        self.mst_cache[food] = (graph, mst_cost)
        return mst_cost

    def _mst_by_diff(self, state: MyGameState, pred: MyGameState) -> int:
        pred_graph, mst_cost = self.mst_cache[pred.food]
        graph = pred_graph.deep_copy()
        pred_food = pred.food
        food = state.food

        # Often the MST will be very similar to the predecessor's MST.
        # Here we try to take advantage of that.

        # Is there only one food difference?
        missing_food = []
        for x in range(food.width):
            for y in range(food.height):
                if food[x][y] != pred_food[x][y]:
                    # We found a difference
                    assert pred_food[x][y], "Successor grid cannot have more food"
                    missing_food.append((x, y))
        assert len(missing_food) > 0

        for missing in missing_food:
            for node in graph.nodes:
                # FIXME: If more than one is missing, always start with the one with fewest edges (leaf nodes)
                if node.x != missing[0] or node.y != missing[1]:
                    continue

                if len(node.edges) == 1:
                    # Missing food is a leaf node, so we still have an MST when we remove it!
                    mst_cost = mst_cost - node.edges[0].weight
                    graph.remove_node(node.index)
                    break

                # Missing food is not a leaf node. Removing the node will create disconnected trees,
                # but the shortest edges that connects the trees again creates the new spanning tree.

                # Disconnect trees
                tree_roots = []
                for edge in node.edges:
                    if edge.i != node.index:
                        tree_roots.append(graph.nodes[edge.i])
                    elif edge.j != node.index:
                        tree_roots.append(graph.nodes[edge.j])
                    mst_cost -= edge.weight
                graph.remove_node(node.index)

                if len(graph.nodes) == 0:
                    # This was last the node!
                    self.mst_cache[food] = (graph, 0)
                    return 0

                assert len(tree_roots) > 1
                # Convert each tree root to a list of nodes
                trees = []
                for root in tree_roots:
                    tree = []
                    queue = [root]
                    while queue:
                        n = queue.pop()
                        tree.append(n)
                        for e in n.edges:
                            if e.i != n.index and graph.nodes[e.i] not in tree:
                                queue.append(graph.nodes[e.i])
                            elif e.j != n.index and graph.nodes[e.j] not in tree:
                                queue.append(graph.nodes[e.j])
                    trees.append(tree)

                # Connect trees
                yggdrasil = trees.pop()
                while trees:
                    nearest = None, None, None  # node, anchor, tree index
                    nearest_cost = Distances.BIG_NUMBER
                    for i, tree in enumerate(trees):
                        for n in tree:
                            for ygg_node in yggdrasil:
                                d = self.distances.get((n.x, n.y), (ygg_node.x, ygg_node.y))
                                if d < nearest_cost:
                                    nearest_cost = d
                                    nearest = n, ygg_node, i
                    graph.add_edge(nearest[0].index, nearest[1].index, nearest_cost)
                    mst_cost += nearest_cost
                    yggdrasil += trees.pop(nearest[2])

                break

        self.mst_cache[food] = (graph, mst_cost)
        return mst_cost


def dist_to_closest_ghost(distances: Distances, state: MyGameState) -> int:
    nearest_ghost_dist = 999999999999
    for ghost in state.ghosts:
        dist = distances.get(state.pacman, ghost.position)
        if dist < nearest_ghost_dist:
            nearest_ghost_dist = dist
    return nearest_ghost_dist


def dist_to_closest_food(distances: Distances, source: Tuple[int, int], food: game.Grid) -> int:
    if food[source[0]][source[1]]:
        return 0
    closest_food_dist = distances.BIG_NUMBER
    for x in range(distances.walls.width):
        for y in range(distances.walls.height):
            if food[x][y]:
                dist = distances.get((x, y), source)
                if dist < closest_food_dist:
                    closest_food_dist = dist
    return closest_food_dist
