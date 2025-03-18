import random
import time
from typing import Dict, Tuple, List

from nicolaj.my_state import MyGameState
from nicolaj.static_info import StaticInfo
from pacman import GameState


COST_OF_LOSING = 999999


def heuristic(static_info: StaticInfo, state: MyGameState) -> float:
    if state.is_loss():
        return COST_OF_LOSING
    if state.is_win():
        return 0

    furthest_dist = 0
    closest_dist = state.food.width * state.food.height
    for x in range(state.food.width):
        for y in range(state.food.height):
            if state.food[x][y]:
                dist = abs(state.pacman[0] - x) + abs(state.pacman[1] - y)
                if dist < closest_dist:
                    closest_dist = dist
                if dist > furthest_dist:
                    furthest_dist = dist

    count_left = state.food.count()
    return max(count_left + closest_dist - 1, furthest_dist)


class TTEntry:
    def __init__(self):
        self.expected_cost = 0
        self.explored = False
        self.successors: Dict[Tuple[int, int], List[Tuple[MyGameState, float]]] = {}
        self.done = False
        self.best_action = (0, 0)


class PolicyRefiner:
    def __init__(self, static_info: StaticInfo):
        self.static_info = static_info
        s = GameState()
        s.initialize(static_info.layout)
        self.root_state: MyGameState = MyGameState.extract(s)
        self.transposition_table = {}
        self.trials_completed = 0

    def refine(self, stop_at: float):
        # Labelled RTDP
        print('Refining policy (LRTDP)...')
        while time.time() < stop_at:
            s = self.root_state
            trial = [s]
            explorations_left = 100
            while True:
                if time.time() >= stop_at:
                    return

                tt = self.transposition_table.setdefault(s, TTEntry())

                # Should trial stop in this state?
                if tt.done and s == self.root_state:
                    print('Root is done!')
                    return
                if s.is_loss():
                    tt.expected_cost = COST_OF_LOSING
                    tt.best_action = (0, 0)
                    tt.done = True
                    break
                elif s.is_win():  # Must be elif as loss takes prioritization
                    tt.expected_cost = 0
                    tt.best_action = (0, 0)
                    tt.done = True
                    break
                elif explorations_left <= 0:
                    break

                # Explore if needed
                if not tt.explored:
                    tt.successors = {act: list(outs) for act, outs in s.generate_successors_map(self.static_info)}
                    tt.explored = True
                    explorations_left -= 1

                # Update expected cost and best action
                self._update_best_action(tt)

                # Sample best action successor to get next state - but don't visit done states
                sum_prob = 0
                not_done_succs = []
                for succ, prob in tt.successors[tt.best_action]:
                    if self.transposition_table[succ].done:
                        continue
                    not_done_succs.append((succ, prob))
                    sum_prob += prob
                if len(not_done_succs) == 0:
                    break  # All successors are done (or there are none), so s is terminal
                rn = random.random() * sum_prob
                for succ, prob in not_done_succs:
                    rn -= prob
                    if rn <= 0:
                        s = succ
                        trial.append(s)
                    break

            for i, s in enumerate(reversed(trial)):
                done = True
                tt = self.transposition_table[s]
                if not s.is_loss() and not s.is_win():
                    self._update_best_action(tt)
                    if len(tt.successors) != 0:  # Terminal states have no successors
                        for succ, prob in tt.successors[tt.best_action]:
                            if succ not in self.transposition_table:
                                done = False
                                break
                            if not self.transposition_table[succ].done:
                                done = False
                                break
                tt.done = done

            self.trials_completed += 1
            if self.trials_completed % 500 == 0:
                print('Trials completed:', self.trials_completed)

    def _update_best_action(self, tt: TTEntry):
        tt.best_action = (0, 0)
        tt.expected_cost = COST_OF_LOSING + 1
        for act, outs in tt.successors.items():
            cost = 1.5 if act == (0, 0) else 1.0
            for succ, prob in outs:
                if succ not in self.transposition_table:
                    ttsucc = TTEntry()
                    self.transposition_table[succ] = ttsucc
                    ttsucc.expected_cost = heuristic(self.static_info, succ)
                cost += prob * self.transposition_table[succ].expected_cost
            if cost < tt.expected_cost:
                tt.best_action = act
                tt.expected_cost = cost

    def get_value(self, state: MyGameState):
        if tt := self.transposition_table.get(hash(state)):
            return tt.expected_value
        return heuristic(self.static_info, state)

    def get_action(self, state: MyGameState) -> Tuple[int, int]:
        tt = self.transposition_table[state]
        print('Lookup:', tt.best_action, ', expected cost:', tt.expected_cost)
        return tt.best_action
