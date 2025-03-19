import heapq
from functools import cache
from typing import Tuple

import game
from nicolaj.my_state import COST_OF_LOSING, MyGameState


@cache
def distance(walls: game.Grid, source: Tuple[int, int], destination: Tuple[int, int]) -> int:
    # Djikstra's algorithm

    width, height = walls.width, walls.height
    ax, ay = source
    bx, by = destination

    assert not walls[ax][ay] and not walls[bx][by]

    queue = [(0, ax, ay)]  # (cost, x, y) - not a priority queue since all edge have cost 1
    visited = set()

    while queue:
        cost, x, y = queue.pop(0)

        if (x, y) in visited:
            continue
        visited.add((x, y))

        if (x, y) == (bx, by):
            return cost

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not walls[nx][ny]:
                queue.append((cost + 1, nx, ny))

    assert False


@cache
def food_mst_size(walls: game.Grid, food: game.Grid) -> int:
    # NOTE: The size is off-by-minus-one depending on how you understand size of mst
    positions = [(x, y) for x in range(food.width) for y in range(food.height) if food[x][y]]

    # Prim's algorithm
    mst_cost = 0
    visited = set()
    pq = [(0, positions[0][0], positions[0][1])]  # (cost, x, y)

    while pq and len(visited) < len(positions):
        cost, x, y = heapq.heappop(pq)

        if (x, y) in visited:
            continue
        visited.add((x, y))
        mst_cost += cost

        for nx, ny in positions:
            if (nx, ny) not in visited:
                d = distance(walls, (x, y), (nx, ny))
                heapq.heappush(pq, (d, nx, ny))

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

    closest_food_dist = walls.width * walls.height
    for x in range(walls.width):
        for y in range(walls.height):
            if state.food[x][y]:
                dist = distance(walls, (x, y), state.pacman)
                if dist < closest_food_dist:
                    closest_food_dist = dist

    food_count = state.food.count()
    if food_count > 100:
        # There is a lot of food which makes MST expensive.
        # The density of food makes it likely that it is just one cluster anyway.
        if exactly_one_food_cluster(state.food):
            return food_count

    return food_mst_size(walls, state.food) + approach1(closest_food_dist)
