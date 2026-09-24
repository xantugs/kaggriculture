"""Evaluate complete reactive candidate policies in isolated sampled worlds.

This is the planning/evaluation core, not a ready-to-submit farm agent. Candidate
generation and opponent belief estimation are deliberately explicit interfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import statistics
import time
from typing import Callable

from world import World


@dataclass(frozen=True)
class Candidate:
    name: str
    make_policy: Callable


@dataclass
class Evaluation:
    name: str
    margins: list[float] = field(default_factory=list)
    own_cash: list[float] = field(default_factory=list)
    rival_cash: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    completed: bool = False
    seconds: float = 0.0

    @property
    def score(self):
        if not self.completed:
            raise ValueError('cannot rank an incomplete evaluation')
        outcomes = [1.0 if m > 0 else 0.5 if m == 0 else 0.0 for m in self.margins]
        # These are sampled-world results, not calibrated real win probabilities.
        return (statistics.mean(outcomes), statistics.mean(self.margins), min(self.margins))

    def as_dict(self):
        return {'name': self.name, 'completed': self.completed, 'margins': self.margins,
                'own_cash': self.own_cash, 'rival_cash': self.rival_cash,
                'score': self.score if self.completed else None,
                'errors': self.errors, 'seconds': self.seconds}


def rank_candidates(candidates, worlds, seat, opponent_factory, *, max_seconds=None):
    """Score terminal cash margins; each candidate gets identical scenario roots.

    Factories receive only their own observation. They must return fresh policies
    with `act(observation, configuration)`. No live baseline state is mutated.
    A deadline discards partial candidate evaluations instead of ranking short runs.
    """
    if not candidates or not worlds:
        raise ValueError('candidates and worlds must be nonempty')
    if len({c.name for c in candidates}) != len(candidates):
        raise ValueError('candidate names must be unique')
    deadline = float('inf') if max_seconds is None else time.perf_counter() + max_seconds
    results = []
    for candidate in candidates:
        result = Evaluation(candidate.name)
        start = time.perf_counter()
        for root in worlds:
            if time.perf_counter() >= deadline:
                result.errors.append('planning budget exhausted')
                break
            world = root.fork()
            try:
                ours = candidate.make_policy(world.observation(seat))
                rival = opponent_factory(world.observation(1-seat))
                policies = [None, None]
                policies[seat], policies[1-seat] = ours, rival
                while not world.done:
                    if time.perf_counter() >= deadline:
                        raise TimeoutError('planning budget exhausted')
                    # Both actions are chosen before either is executed.
                    actions = [policies[i].act(world.observation(i), world.policy_configuration()) for i in range(2)]
                    world.advance(actions)
                cash = world.cash()
                result.own_cash.append(cash[seat])
                result.rival_cash.append(cash[1-seat])
                result.margins.append(world.final_margin(seat))
            except Exception as exc:
                result.errors.append(f'{type(exc).__name__}: {exc}')
                break
        result.completed = len(result.margins) == len(worlds) and not result.errors
        result.seconds = time.perf_counter() - start
        results.append(result)
    eligible = [r for r in results if r.completed]
    best = max(eligible, key=lambda r: r.score) if eligible else None
    return best, results
