"""Run integration parity and a controlled multi-day planning demonstration."""
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from harness import _load_agent_module, make
from world import K, World, PASS
from search import Candidate, rank_candidates


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def parity(seed):
    """Compare every public/private transition with the actual framework run."""
    a = _load_agent_module(ROOT / 'arena/cand/omw_v12.py')
    b = _load_agent_module(ROOT / 'arena/cand/omw_v11.py')
    env = make('kaggriculture', debug=True, configuration={'seed': seed})
    base_interpreter = env.interpreter
    shadow = None
    checked = 0

    def interpreter(state, environment):
        nonlocal shadow, checked
        obs = state[0].observation
        if getattr(obs, 'farms', None) and int(obs.get('step', 0)) >= 144:
            if shadow is None:
                shadow = World.from_snapshot_for_validation(state, environment.configuration, environment.info)
            step = int(obs['step'])
            shadow.advance([copy.deepcopy(s.action) for s in state])
            out = base_interpreter(state, environment)
            for seat in range(2):
                actual = {k: state[0].observation[k] for k in ('farms', 'market', 'town', 'day', 'hour')}
                actual.update(step=step + 1, player=seat, private=state[seat].observation.private,
                              remainingOverageTime=60)
                assert shadow.observation(seat) == actual, (seed, step, seat)
                assert shadow.state[seat].status == state[seat].status, (seed, step, 'status')
            checked += 1
            return out
        return base_interpreter(state, environment)

    env.interpreter = interpreter
    env.run([a.agent, b.agent])
    assert checked == 575, checked
    assert shadow.done
    rewards = [s.reward for s in env.steps[-1]]
    assert shadow.cash() == rewards
    return {'seed': seed, 'transitions_checked': checked,
            'both_private_states_checked': True, 'terminal_cash': rewards}


class CropPlan:
    """Complete two-crop job package for the controlled demo, not a farm policy."""
    def __init__(self, wheat, carrot):
        self.wheat = wheat
        self.carrot = carrot
        q = int(wheat) + int(carrot)
        self.commands = {
            624: ['PICKUP', 'FERTILIZER', q] if q else ['PASS'],
            625: ['FERTILIZE'] if wheat else ['PASS'], 626: ['WATER'], 627: ['WEST'],
            628: ['FERTILIZE'] if carrot else ['PASS'], 629: ['WATER'], 630: ['EAST'], 631: ['DROP'],
            648: ['WATER'], 649: ['HARVEST'], 650: ['WEST'], 651: ['WATER'],
            652: ['HARVEST'], 653: ['EAST'], 654: ['DROP'],
        }

    def act(self, obs, cfg):
        step = int(obs['step'])
        command = self.commands.get(step, ['PASS'])
        stock = dict(obs['private']['shed'])
        if command[0] == 'PICKUP':
            stock[command[1]] = max(0, stock.get(command[1], 0) - command[2])
        elif command[0] == 'DROP':
            for item, q in obs['private']['inventories'][0].items():
                stock[item] = stock.get(item, 0) + q
        market = [['SELL', item, q] for item, q in sorted(stock.items()) if q > 0]
        return {'farmer': command, 'hands': [], 'market': market}


class RivalSeller:
    def act(self, obs, cfg):
        market = []
        if int(obs['step']) >= 654:
            market = [['SELL', item, q] for item, q in sorted(obs['private']['shed'].items()) if q]
        return {'farmer': ['PASS'], 'hands': [], 'market': market}


def demo_world(fertilizer_inventory, opponent_carrots):
    base = World.new_for_validation(17)
    obs = base.observation(0)
    obs.update(step=624, day=26, hour=0)
    for farm in obs['farms']:
        farm['money'] = 1000.0
    farm = obs['farms'][0]
    farm['tiles'][4][4] = K._new_plant('WHEAT', 23, 24)
    farm['tiles'][4][4].update(yield_units=2, consecutive_unwatered=0)
    farm['tiles'][4][3] = K._new_plant('CARROT', 24, 24)
    farm['tiles'][4][3]['consecutive_unwatered'] = 0
    obs['private']['shed'] = {'FERTILIZER': 2}
    obs['market']['inventory']['FERTILIZER'] = fertilizer_inventory
    obs['market']['inventory']['CARROT'] = 9450
    K._refresh_prices(obs['market'])
    # All eight shops are already observed. No future shop information is used.
    obs['town']['unlocked_shops'] = ['BAKERY'] * 8
    estimate = K._new_private()
    estimate['shed'] = {'CARROT': opponent_carrots, 'FERTILIZER': 25}
    world = World.from_observation(obs, {'seed': 999999},
                                   opponent_private=estimate, scenario_seed=121)
    assert world.env.info['seed'] == 121
    assert world.policy_configuration()['seed'] is None
    assert world.observation(0)['private'] == obs['private']
    assert world.observation(1)['private'] == estimate
    assert 'opponent_private' not in world.observation(0)
    return world


def planning_demo():
    candidates = [Candidate(name, lambda obs, w=w, c=c: CropPlan(w, c))
                  for name, w, c in [('sell_fertilizer', False, False),
                                     ('fertilize_wheat', True, False),
                                     ('fertilize_carrot', False, True),
                                     ('fertilize_both', True, True)]]
    output = {}
    for name, inv in [('cheap_fertilizer', 10450), ('expensive_fertilizer', 10000)]:
        worlds = [demo_world(inv, carrots) for carrots in (5, 15)]
        before = [digest(w.state) for w in worlds]
        best, evaluations = rank_candidates(candidates, worlds, 0, lambda obs: RivalSeller())
        assert all(e.completed for e in evaluations), [e.as_dict() for e in evaluations]
        assert before == [digest(w.state) for w in worlds], 'planning mutated observed roots'
        output[name] = {'selected': best.name, 'evaluations': [e.as_dict() for e in evaluations]}
    assert output['cheap_fertilizer']['selected'] == 'fertilize_both', output
    assert output['expensive_fertilizer']['selected'] == 'sell_fertilizer', output

    # An exhausted search must not promote a partially evaluated plan.
    best, rows = rank_candidates(candidates, [demo_world(10450, 5)], 0,
                                lambda obs: RivalSeller(), max_seconds=0)
    assert best is None and not any(r.completed for r in rows)
    output['deadline_discards_partial_results'] = True
    output['limitations'] = 'Controlled two-crop demo. It demonstrates multi-day candidate evaluation, not improvement over v12 or an executable full-farm planner.'
    return output


if __name__ == '__main__':
    result = {'parity': [], 'planning_demo': planning_demo()}
    print(json.dumps({'demo': {k: v['selected'] for k, v in result['planning_demo'].items()
                               if isinstance(v, dict) and 'selected' in v}}), flush=True)
    for seed in (210001, 1461186332):
        row = parity(seed)
        result['parity'].append(row)
        print(json.dumps(row), flush=True)
    target = Path(__file__).with_name('verification.json')
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Verified; report saved to ' + str(target), flush=True)
