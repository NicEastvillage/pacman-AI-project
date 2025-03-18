import time

import game
from layout import Layout
from nicolaj.graph import MyDirection
from nicolaj.my_state import MyGameState
from nicolaj.rldp import PolicyRefiner, heuristic
from nicolaj.static_info import StaticInfo
from pacman import GameState


class PlanningAgent(game.Agent):

    def __init__(self, layout: Layout, **kwargs):
        super().__init__(**kwargs)
        self.layout: Layout = layout
        self.static_info: StaticInfo = StaticInfo(layout)
        self.policy = PolicyRefiner(self.static_info)
        self.offline_planning()

    def offline_planning(self):
        # Time limit: 10 minutes

        stop_at = time.time() + 2 * 60  # TODO: Extend to 10 min
        self.policy.refine(stop_at)

    def getAction(self, state: GameState):
        # Time limit: approx 1 second
        stop_at = time.time() + 0.95
        s = MyGameState.extract(state)

        print('Heuristic in this state:', heuristic(self.static_info, s))
        self.policy.root_state = s
        self.policy.refine(stop_at)

        act = MyDirection.toStr[self.policy.get_action(s)]
        return act
