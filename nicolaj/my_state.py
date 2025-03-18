from typing import Tuple, List, Iterator

import game
from nicolaj.graph import MyDirection
from nicolaj.static_info import StaticInfo
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
        self.ghosts.sort()

    @staticmethod
    def extract(state: GameState) -> 'MyGameState':
        return MyGameState(
            state.getPacmanState().getPosition(),
            list(Ghost.extract(g) for g in state.getGhostStates()),
            state.getFood(),
        )

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

    def generate_successors_map(self, static_info: StaticInfo) -> Iterator[
        Tuple[Tuple[int, int], Iterator[Tuple['MyGameState', float]]]]:
        if self.is_loss() or self.is_win():
            return

        ignore_stop_act = True
        for ghost in self.ghosts:
            dist = abs(ghost.position[0] - self.pacman[0]) + abs(ghost.position[1] - self.pacman[1])
            if dist <= 2:
                ignore_stop_act = False
                break


        for act in static_info.get_all_legal_actions(self.pacman):
            if act == (0, 0) and ignore_stop_act:
                continue
            wip_succ = self.generate_pacman_successor(act)
            yield act, self._generate_ghost_responses(static_info, 0, wip_succ, 1.0)

    def _generate_ghost_responses(self, static_info: StaticInfo, ghost_index: int, wip_succ: 'MyGameState',
                                  probability: float) -> Iterator[Tuple['MyGameState', float]]:
        if ghost_index >= len(self.ghosts):
            # No more ghosts
            yield wip_succ, probability
        else:
            ghost = self.ghosts[ghost_index]
            actions = static_info.get_ghost_legal_actions(ghost.position, ghost.direction)
            for act in actions:
                next_succ = wip_succ.generate_ghost_successor(ghost_index, act)
                yield from self._generate_ghost_responses(static_info, ghost_index + 1, next_succ,
                                                          probability / len(actions))
