import random
import time
from typing import Dict, Tuple, List

import game
from nicolaj.heuristic import heuristic
from nicolaj.my_state import MyGameState, COST_OF_LOSING


GAMMA_INV = 1.0/0.97


class TTEntry:
    def __init__(self):
        self.heuristic_cost = 0
        self.expected_cost = 0
        self.explored = False
        self.successors: Dict[Tuple[int, int], List[Tuple[MyGameState, float]]] = {}
        self.done = False
        self.best_action = (0, 0)


class PolicyRefiner:
    def __init__(self, walls: game.Grid, root_state: MyGameState):
        self.walls = walls
        self.root_state = root_state
        self.transposition_table = {}
        self.trials_completed = 0

    def refine(self, stop_at: float, report_regularly: bool = False):
        # Labelled RTDP
        print('Refining policy (L-RTDP)...')
        report_at = time.time() + 20 if report_regularly else stop_at + 10000
        while time.time() < stop_at:
            s = self.root_state
            trial = [s]
            explorations_left = 10
            while True:
                if time.time() + 0.01 >= stop_at:
                    break  # +0.01 so we have time to learn from this last trial

                tt = self.transposition_table.setdefault(s, TTEntry())

                # Should trial stop in this state?
                if tt.done and s == self.root_state:
                    print('... Root is done!')
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
                    # We have explored enough. s will not be a part of our trial
                    trial.pop()
                    break

                # Explore if needed
                if not tt.explored:
                    tt.successors = {act: list(outs) for act, outs in s.generate_successors_map(self.walls)}
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
            if time.time() >= report_at:
                print('...Trials:', self.trials_completed, '...')
                report_at += 20

    def _update_best_action(self, tt: TTEntry):
        tt.best_action = (0, 0)
        tt.expected_cost = COST_OF_LOSING + 1
        for act, outs in tt.successors.items():
            cost = 1.5 if act == (0, 0) else 1.0
            for succ, prob in outs:
                if succ not in self.transposition_table:
                    ttsucc = TTEntry()
                    self.transposition_table[succ] = ttsucc
                    ttsucc.heuristic_cost = heuristic(self.walls, succ)
                    ttsucc.expected_cost = ttsucc.heuristic_cost
                cost += prob * self.transposition_table[succ].expected_cost * GAMMA_INV
            if cost < tt.expected_cost:
                tt.best_action = act
                tt.expected_cost = cost

    def get_action(self, state: MyGameState) -> Tuple[Tuple[int, int], float]:
        tt = self.transposition_table[state]
        return tt.best_action, tt.expected_cost
