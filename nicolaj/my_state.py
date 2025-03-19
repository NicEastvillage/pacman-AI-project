from typing import Tuple, List, Iterator

import game
from nicolaj.direction import MyDirection
from pacman import GameState

COST_OF_LOSING = 999999


class Ghost:
    def __init__(self, position: Tuple[int, int], direction: Tuple[int, int]):
        self.position = position
        self.direction = direction

    def __lt__(self, other):
        if self.position != other.position:
            return self.position < other.position
        return self.direction < other.direction

    @staticmethod
    def extract(agent: game.AgentState):
        x, y = agent.getPosition()
        return Ghost((int(x + 0.5), int(y + 0.5)), MyDirection.fromStr[agent.getDirection()])


class MyGameState:
    def __init__(self, pacman: Tuple[int, int], ghosts: List[Ghost], food: game.Grid):
        # WATCH OUT: Each of these may be shared with other game states
        self.pacman = pacman
        self.ghosts = ghosts
        self.food = food

    @staticmethod
    def extract(state: GameState) -> 'MyGameState':
        return MyGameState(
            state.getPacmanState().getPosition(),
            list(Ghost.extract(g) for g in state.getGhostStates()),
            state.getFood(),
        )

    def normalize(self):
        # WATCH OUT: Changes hash
        self.ghosts.sort()

    def is_win(self):
        return self.food.count() == 0

    def is_loss(self):
        for ghost in self.ghosts:
            if ghost.position == self.pacman:
                return True
            dx, dy = ghost.direction
            if (ghost.position[0] - dx, ghost.position[1] - dy) == self.pacman:
                return True  # We have just walked into the ghost (ghosts move slightly slower)
        return False

    def generate_pacman_successor(self, act: Tuple[int, int]) -> 'MyGameState':
        new_pacman = (self.pacman[0] + act[0], self.pacman[1] + act[1])
        new_food = self.food
        if self.food[new_pacman[0]][new_pacman[1]]:
            new_food = self.food.deepCopy()
            new_food[new_pacman[0]][new_pacman[1]] = False
        return MyGameState(new_pacman, self.ghosts, new_food)

    def generate_ghost_successor(self, ghost_index: int, act: Tuple[int, int]) -> 'MyGameState':
        old_ghost = self.ghosts[ghost_index]
        new_position = (old_ghost.position[0] + act[0], old_ghost.position[1] + act[1])
        new_ghost_list = self.ghosts.copy()
        new_ghost_list[ghost_index] = Ghost(new_position, act)
        return MyGameState(self.pacman, new_ghost_list, self.food)

    def generate_successors_map(self, walls: game.Grid) -> Iterator[
        Tuple[Tuple[int, int], Iterator[Tuple['MyGameState', float]]]]:
        if self.is_loss() or self.is_win():
            return

        ignore_stop_act = True
        for ghost in self.ghosts:
            dist = abs(ghost.position[0] - self.pacman[0]) + abs(ghost.position[1] - self.pacman[1])
            if dist <= 2:
                ignore_stop_act = False
                break

        for act in get_all_legal_actions(walls, self.pacman):
            if act == (0, 0) and ignore_stop_act:
                continue
            wip_succ = self.generate_pacman_successor(act)
            yield act, self._generate_ghost_responses(walls, 0, wip_succ, 1.0)

    def _generate_ghost_responses(self, walls: game.Grid, ghost_index: int, wip_succ: 'MyGameState',
                                  probability: float) -> Iterator[Tuple['MyGameState', float]]:
        if ghost_index >= len(self.ghosts):
            # No more ghosts
            wip_succ.normalize()
            yield wip_succ, probability
        else:
            ghost = self.ghosts[ghost_index]
            actions = get_ghost_legal_actions(walls, ghost.position, ghost.direction)
            for act in actions:
                next_succ = wip_succ.generate_ghost_successor(ghost_index, act)
                yield from self._generate_ghost_responses(walls, ghost_index + 1, next_succ,
                                                          probability / len(actions))


def get_all_legal_actions(walls: game.Grid, position: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    x, y = position
    for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South, (0, 0)]:
        if not walls[x + dx][y + dy]:
            yield dx, dy


def get_ghost_legal_actions(walls: game.Grid, position: Tuple[int, int], direction: Tuple[int, int]) -> List[
    Tuple[int, int]]:
    actions = []
    x, y = position
    assert not walls[x][y]
    for dx, dy in [MyDirection.North, MyDirection.East, MyDirection.West, MyDirection.South]:
        if not walls[x + dx][y + dy]:
            actions.append((dx, dy))
    if len(actions) > 1 and MyDirection.opposite[direction] in actions:
        actions.remove(MyDirection.opposite[direction])
    elif len(actions) == 0:
        actions.append((0, 0))
    return actions
