import time
from typing import Tuple

import game
from layout import Layout
from nicolaj.direction import MyDirection
from nicolaj.heuristic import Distances, Heuristic, dist_to_closest_ghost
from nicolaj.my_state import MyGameState
from nicolaj.naive import get_naive_action
from nicolaj.rldp import PolicyRefiner
from pacman import GameState


class PlanningAgent(game.Agent):

    def __init__(self, layout: Layout, **kwargs):
        super().__init__(**kwargs)
        self.layout: Layout = layout
        self.walls = layout.walls
        self.distances = Distances(self.walls)
        self.heuristic = Heuristic(self.distances)
        self.steps = 0
        ss = GameState()
        ss.initialize(layout)
        self.start_state = MyGameState.extract(ss)
        self.policy = PolicyRefiner(self.heuristic, self.walls, self.start_state)
        self.offline_planning()

    def offline_planning(self):
        # Time limit: 10 minutes

        stop_at = time.time() + 6.5 * 10  # TODO: Extend to 10 min
        print('Size:', self.walls.width, 'x', self.walls.height)
        print('Food:', self.start_state.food.count())
        print('Ghosts:', len(self.start_state.ghosts))
        self.policy.refine(stop_at, True)
        print('Trials:', self.policy.trials_completed)
        print('Offline planning over!')

    def getAction(self, state: GameState):
        # Time limit: approx 1 second
        stop_at = time.time() + 0.95

        self.steps += 1
        print('===== STEP ', self.steps, ' =====')
        s = MyGameState.extract(state)
        self.policy.root_state = s

        food_count = s.food.count()
        ghost_dist = dist_to_closest_ghost(self.distances, s)
        naive = food_count > 90 and ghost_dist > 8 and False

        if naive:
            direction = get_naive_action(self.walls, s)
            expect_cost = '???'

        self.policy.refine(stop_at)
        if not naive:
            direction, expect_cost = self.policy.get_action(s)
        else:
            print('! Feeling overwhelmed, but safe; Choosing action naively !')

        act = MyDirection.toStr[direction]
        print('Food:', food_count)
        print('Ghost dist:', ghost_dist)
        print('Heuristic:', self.heuristic.get(s, None))
        print('Trials:', self.policy.trials_completed)
        print('Action:', direction)
        print('Action expected cost:', expect_cost)
        return act
