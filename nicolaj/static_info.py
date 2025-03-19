from typing import Tuple, Iterator, List

from layout import Layout
from nicolaj.graph import MyDirection


class StaticInfo:
    def __init__(self, layout: Layout):
        self.layout = layout

    def get_all_legal_actions(self, position: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
        x, y = position
        for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South, (0, 0)]:
            if not self.layout.walls[x + dx][y + dy]:
                yield dx, dy

    def get_ghost_legal_actions(self, position: Tuple[int, int], direction: Tuple[int, int]) -> List[Tuple[int, int]]:
        actions = []
        x, y = position
        assert not self.layout.walls[x][y]
        for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South]:
            if not self.layout.walls[x + dx][y + dy]:
                actions.append((dx, dy))
        if len(actions) > 1 and MyDirection.opposite[direction] in actions:
            actions.remove(MyDirection.opposite[direction])
        elif len(actions) == 0:
            actions.append((0, 0))
        return actions
