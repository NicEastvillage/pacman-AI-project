import heapq
from functools import cache
from typing import Tuple

import game
from nicolaj.graph import Graph
from nicolaj.my_state import COST_OF_LOSING, MyGameState


@cache
def distance(walls: game.Grid, source: Tuple[int, int], destination: Tuple[int, int]) -> int:
    # Djikstra's algorithm

    width, height = walls.width, walls.height
    start_x, start_y = source
    end_x, end_y = destination

    assert not walls[start_x][start_y] and not walls[end_x][end_y]

    queue = [(0, start_x, start_y)]  # (cost, x, y) - not a priority queue since all edge have cost 1
    visited = set()

    while queue:
        cost, x, y = queue.pop(0)

        if (x, y) in visited:
            continue
        visited.add((x, y))

        if (x, y) == (end_x, end_y):
            return cost

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not walls[nx][ny]:
                queue.append((cost + 1, nx, ny))

    assert False


def dist_to_closest_food(point: Tuple[int, int], walls: game.Grid, food: game.Grid) -> int:
    if food[point[0]][point[1]]:
        return 0
    closest_food_dist = walls.width * walls.height
    for x in range(walls.width):
        for y in range(walls.height):
            if food[x][y]:
                dist = distance(walls, (x, y), point)
                if dist < closest_food_dist:
                    closest_food_dist = dist
    return closest_food_dist


@cache
def food_mst_size(walls: game.Grid, food: game.Grid) -> int:
    # NOTE: The size is off-by-minus-one depending on how you understand size of mst

    if hasattr(food_mst_size, '_prev_food'):
        # Often the input will be very similar to the last input
        prev_food = food_mst_size._prev_food
        prev_graph = food_mst_size._prev_graph
        diffx, diffy = 0, 0
        diff_count = 0
        for x in range(food.width):
            for y in range(food.height):
                if food[x][y] != prev_food[x][y]:
                    # We found a difference
                    diff_count += 1
                    if diff_count > 1:
                        break
                    if food[x][y]:
                        # New food grid has more food - we have no tricks here
                        diff_count = 2
                        break
                    diffx, diffy = x, y
            if diff_count > 1:
                break
        if diff_count == 1:
            graph = prev_graph
            for node in graph.nodes:
                if node.x == diffx and node.y == diffy:
                    if len(node.edges) == 1:
                        # This is a leaf node, so we can easily find new cost!
                        mst_cost = food_mst_size._prev_cost - node.edges[0].weight
                        graph.remove_node(node.index)
                        food_mst_size._prev_food = food
                        food_mst_size._prev_cost = mst_cost
                        food_mst_size._prev_graph = graph
                        return mst_cost
                    else:
                        # This is not a leaf node, removing it will create disconnected trees,
                        # but the minimum edges that connects the trees again creates the new spanning tree
                        mst_cost = food_mst_size._prev_cost
                        tree_roots = []
                        for edge in node.edges:
                            if edge.i != node.index:
                                tree_roots.append(graph.nodes[edge.i])
                            elif edge.j != node.index:
                                tree_roots.append(graph.nodes[edge.j])
                            mst_cost -= edge.weight
                        graph.remove_node(node.index)

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
                            nearest_cost = 99999999999
                            for i, tree in enumerate(trees):
                                for node in tree:
                                    for ygg_node in yggdrasil:
                                        d = distance(walls, (node.x, node.y), (ygg_node.x, ygg_node.y))
                                        if d < nearest_cost:
                                            nearest_cost = d
                                            nearest = node, ygg_node, i
                            graph.add_edge(nearest[0].index, nearest[1].index, nearest_cost)
                            mst_cost += nearest_cost
                            yggdrasil += trees.pop(nearest[2])

                        food_mst_size._prev_food = food
                        food_mst_size._prev_cost = mst_cost
                        food_mst_size._prev_graph = graph
                        return mst_cost

    graph = Graph()
    for x in range(walls.width):
        for y in range(walls.height):
            if food[x][y]:
                graph.add_node(x, y)

    # Prim's algorithm
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
                d = distance(walls, (node.x, node.y), (other.x, other.y))
                heapq.heappush(pq, (d, other, node))

    food_mst_size._prev_food = food
    food_mst_size._prev_cost = mst_cost
    food_mst_size._prev_graph = graph
    return mst_cost


@cache
def exactly_one_food_cluster(food: game.Grid):
    width, height = food.width, food.height
    marked = game.Grid(width, height)  # Visited cells
    found_one = False

    def flood_fill(x, y):
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < width and 0 <= cy < height):
                continue
            if marked[cx][cy] or not food[cx][cy]:
                continue

            marked[cx][cy] = True

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                stack.append((cx + dx, cy + dy))

    for x in range(width):
        for y in range(height):
            if food[x][y] and not marked[x][y]:
                if found_one:
                    return False
                found_one = True
                flood_fill(x, y)

    return True


def approach1(x: float) -> float:
    return x / (x + 1.0)


def heuristic(walls: game.Grid, state: MyGameState) -> float:
    if state.is_loss():
        return COST_OF_LOSING
    if state.is_win():
        return 0

    closest_food_dist = dist_to_closest_food(state.pacman, walls, state.food)
    return food_mst_size(walls, state.food) + approach1(closest_food_dist)
