import time
from typing import Tuple

import game
from layout import Layout
from nicolaj.direction import MyDirection
from nicolaj.heuristic import distance
from nicolaj.my_state import MyGameState
from nicolaj.naive import get_naive_action
from nicolaj.rldp import PolicyRefiner, heuristic
from pacman import GameState


class PlanningAgent(game.Agent):

    def __init__(self, layout: Layout, **kwargs):
        super().__init__(**kwargs)
        self.layout: Layout = layout
        self.walls = layout.walls
        self.steps = 0
        ss = GameState()
        ss.initialize(layout)
        self.start_state = MyGameState.extract(ss)
        self.policy = PolicyRefiner(self.walls, self.start_state)
        self.offline_planning()

    def offline_planning(self):
        # Time limit: 10 minutes

        stop_at = time.time() + 60  # TODO: Extend to 10 min
        print('Food on this layout:', self.start_state.food.count())
        self.policy.refine(stop_at)
        print('Offline planning over!')

    def getAction(self, state: GameState):
        # Time limit: approx 1 second
        stop_at = time.time() + 0.95

        self.steps += 1
        print('===== STEP ', self.steps, ' =====')
        s = MyGameState.extract(state)
        self.policy.root_state = s
        naive, food, dist = self.do_naive(s)

        if naive:
            print(f'Policy likely underdeveloped - using naive strategy while tons of food left ({food}) and no danger nearby (dist {dist})')
            act = get_naive_action(self.walls, s)
            print('Naive:', act)
            self.policy.refine(stop_at)
            return MyDirection.toStr[act]

        self.policy.refine(stop_at)
        act = MyDirection.toStr[self.policy.get_action(s)]
        return act

    def do_naive(self, state: MyGameState) -> Tuple[bool, int, int]:
        if state.food.count() <= 100:
            return False, 0, 0

        nearest_ghost = None
        nearest_ghost_dist = 0
        for ghost in state.ghosts:
            dist = distance(self.walls, state.pacman, ghost.position)
            if nearest_ghost is None or dist < nearest_ghost_dist:
                nearest_ghost_dist = dist
                nearest_ghost = ghost

        if nearest_ghost_dist <= 8:
            return False, 0, 0

        return True, state.food.count(), nearest_ghost_dist
