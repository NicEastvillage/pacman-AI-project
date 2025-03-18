from typing import Tuple, Iterator, List

import game
from layout import Layout
from nicolaj.graph import MyDirection


class FloydWarshall:
    def __init__(self, walls: game.Grid):
        self.walls = walls
        self.width = walls.width
        self.height = walls.height
        self.dist = [[[[float('inf') for _ in range(self.height)] for _ in range(self.width)]
                      for _ in range(self.height)] for _ in range(self.width)]
        self._compute()

    def _compute(self):
        print('Computing Floyd-Warshall...')
        for x in range(self.width):
            for y in range(self.height):
                self.dist[x][y][x][y] = 0
                if self.walls[x][y]:
                    continue
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if x + dx < 0 or y + dy < 0 or x + dx >= self.width or y + dy >= self.height:
                        continue
                    if not self.walls[x + dx][y + dy]:
                        self.dist[x][y][x + dx][y + dy] = 1
        for kx in range(self.width):
            for ky in range(self.height):
                for ax in range(self.width):
                    for ay in range(self.height):
                        for bx in range(self.width):
                            for by in range(self.height):
                                self.dist[ax][ay][bx][by] = min(self.dist[ax][ay][bx][by], self.dist[ax][ay][kx][ky] + self.dist[kx][ky][bx][by])


class StaticInfo:
    def __init__(self, layout: Layout):
        self.layout = layout
        self.floyd_warshall = FloydWarshall(layout.walls)

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
