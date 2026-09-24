"""Full-season planning world backed by the pinned official interpreter.

Online construction requires an explicit opponent-inventory hypothesis and an
independent scenario seed. It never reconstructs or reads the real hidden seed.
Full-state snapshots are provided separately for offline differential validation.
"""
from __future__ import annotations

import contextlib
import copy
import io
import warnings

with warnings.catch_warnings(), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    warnings.simplefilter('ignore')
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    from kaggle_environments.utils import Struct, structify


PUBLIC = ('farms', 'market', 'town', 'day', 'hour', 'step')
PASS = {'farmer': ['PASS'], 'hands': [], 'market': []}


def configuration(overrides=None):
    cfg = {}
    for key, value in K.specification['configuration'].items():
        if isinstance(value, dict) and 'default' in value:
            cfg[key] = value['default']
        elif not isinstance(value, dict):
            cfg[key] = value
    cfg.setdefault('episodeSteps', 720)
    cfg.setdefault('actTimeout', 1)
    if overrides:
        cfg.update(dict(overrides))
    cfg['seed'] = None
    return structify(cfg)


class Environment:
    def __init__(self, cfg, scenario_seed):
        self.configuration = configuration(cfg)
        self.info = {'seed': int(scenario_seed)}
        self.done = False


class World:
    def __init__(self, state, env):
        self.state = state
        self.env = env

    @classmethod
    def new_for_validation(cls, seed, cfg=None):
        """Start a seeded offline game; never used to infer a competition seed."""
        env = Environment(cfg, seed)
        env.configuration.seed = seed
        state = [Struct(observation=Struct(step=0, player=i, remainingOverageTime=60),
                        action=None, reward=0, status='ACTIVE', info=Struct()) for i in range(2)]
        K.interpreter(state, env)
        env.configuration.seed = None
        return cls(state, env)

    @classmethod
    def from_observation(cls, obs, cfg, *, opponent_private, scenario_seed):
        """Create one belief world from public information and explicit hypotheses.

        `opponent_private` is an estimate supplied by an opponent model, not a
        hidden field obtained from the environment. Future events use scenario_seed.
        """
        seat = int(obs['player'])
        if seat not in (0, 1):
            raise ValueError('expected two-player seat')
        public = copy.deepcopy({key: obs[key] for key in PUBLIC})
        privates = [None, None]
        privates[seat] = copy.deepcopy(obs['private'])
        privates[1-seat] = copy.deepcopy(opponent_private)
        for i, private in enumerate(privates):
            if not isinstance(private, dict) or not all(k in private for k in ('shed', 'seeds', 'inventories')):
                raise ValueError('incomplete private inventory hypothesis')
            if len(private['inventories']) != 1 + len(public['farms'][i]['hands']):
                raise ValueError('inventory hypothesis does not match visible workers')
            for bag in [private['shed'], private['seeds'], *private['inventories']]:
                if any(not isinstance(q, int) or isinstance(q, bool) or q < 0 for q in bag.values()):
                    raise ValueError('invalid inventory quantity')
        shared = structify(public)
        state = []
        for i in range(2):
            observation = Struct(player=i, private=structify(privates[i]), remainingOverageTime=60)
            for key in PUBLIC:
                setattr(observation, key, shared[key])
            state.append(Struct(observation=observation, action=None, reward=0, status='ACTIVE', info=Struct()))
        return cls(state, Environment(cfg, scenario_seed))

    @classmethod
    def from_snapshot_for_validation(cls, state, cfg, env_info):
        """Clone an offline evaluator snapshot including its known test randomness."""
        env = Environment(cfg, env_info['seed'])
        env.info = copy.deepcopy(dict(env_info))
        env.done = all(s['status'] != 'ACTIVE' for s in state)
        return cls(copy.deepcopy(state), env)

    @property
    def step_number(self):
        return int(self.state[0].observation.step)

    @property
    def done(self):
        return self.env.done

    def fork(self):
        return copy.deepcopy(self)

    def observation(self, seat):
        """Policy boundary: exposes only this player's private data."""
        shared = self.state[0].observation
        obs = {key: shared[key] for key in PUBLIC}
        obs.update(player=seat, private=self.state[seat].observation.private,
                   remainingOverageTime=60)
        return structify(copy.deepcopy(obs))

    def policy_configuration(self):
        cfg = copy.deepcopy(self.env.configuration)
        cfg.seed = None
        return cfg

    def advance(self, actions):
        if self.done:
            raise RuntimeError('cannot advance a finished game')
        if len(actions) != 2 or any(not isinstance(a, dict) for a in actions):
            raise ValueError('expected two action dictionaries')
        step = self.step_number
        for seat, action in enumerate(actions):
            self.state[seat].action = structify(copy.deepcopy(action))
        K.interpreter(self.state, self.env)
        for s in self.state:
            s.observation.step = step + 1
        self.env.done = all(s.status != 'ACTIVE' for s in self.state)

    def cash(self):
        return [float(f['money']) for f in self.state[0].observation.farms]

    def final_margin(self, seat):
        if not self.done:
            raise ValueError('terminal cash objective requires a complete continuation')
        cash = self.cash()
        return cash[seat] - cash[1-seat]
