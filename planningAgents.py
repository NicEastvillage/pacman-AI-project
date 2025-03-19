import time

import game
from layout import Layout
from nicolaj.graph import MyDirection
from nicolaj.my_state import MyGameState
from nicolaj.rldp import PolicyRefiner, heuristic
from pacman import GameState


class PlanningAgent(game.Agent):

    def __init__(self, layout: Layout, **kwargs):
        super().__init__(**kwargs)
        self.layout: Layout = layout
        self.walls = layout.walls
        ss = GameState()
        ss.initialize(layout)
        self.start_state = MyGameState.extract(ss)
        self.policy = PolicyRefiner(self.walls, self.start_state)
        self.offline_planning()

    def offline_planning(self):
        # Time limit: 10 minutes

        stop_at = time.time() + 60  # TODO: Extend to 10 min
        print('Warming up caches...')
        heuristic(self.walls, self.start_state)

        self.policy.refine(stop_at)

    def getAction(self, state: GameState):
        # Time limit: approx 1 second
        stop_at = time.time() + 0.95
        s = MyGameState.extract(state)

        self.policy.root_state = s
        self.policy.refine(stop_at)

        act = MyDirection.toStr[self.policy.get_action(s)]
        return act
