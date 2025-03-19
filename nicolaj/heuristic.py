import heapq
from functools import cache
from typing import Tuple

import game
from nicolaj.my_state import COST_OF_LOSING, MyGameState
from nicolaj.static_info import StaticInfo


@cache
def distance(walls: game.Grid, source: Tuple[int, int], destination: Tuple[int, int]) -> int:
    # Djikstra's algorithm

    width, height = walls.width, walls.height
    ax, ay = source
    bx, by = destination

    assert not walls[ax][ay] and not walls[bx][by]

    priority_queue = [(0, ax, ay)]  # (cost, x, y)
    visited = set()

    while priority_queue:
        cost, x, y = heapq.heappop(priority_queue)

        if (x, y) in visited:
            continue
        visited.add((x, y))

        if (x, y) == (bx, by):
            return cost

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and not walls[nx][ny]:
                heapq.heappush(priority_queue, (cost + 1, nx, ny))

    assert False


@cache
def visit_food_mst_size(walls: game.Grid, food: game.Grid, pacman: Tuple[int, int]) -> int:
    # NOTE: The size is off-by-minus-one depending on how you understand size of mst
    positions = [(x, y) for x in range(food.width) for y in range(food.height) if food[x][y]] + [pacman]

    # Prim's algorithm
    mst_cost = 0
    visited = set()
    pq = [(0, pacman[0], pacman[1])]  # (cost, x, y)

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


def heuristic(static_info: StaticInfo, state: MyGameState) -> float:
    if state.is_loss():
        return COST_OF_LOSING
    if state.is_win():
        return 0

    return visit_food_mst_size(static_info.layout.walls, state.food, state.pacman)
