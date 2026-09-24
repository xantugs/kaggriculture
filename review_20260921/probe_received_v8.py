"""Read-only agent review; records actual filled sales and adaptive-layer telemetry."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from harness import _load_agent_module, make
from kaggle_environments.envs.kaggriculture import kaggriculture as K

SOURCE = Path(r'C:\Users\khant\Downloads\main (2).py')


def run(seed):
    mod = _load_agent_module(SOURCE)
    rival = _load_agent_module(ROOT / 'submit/tape_a2/main.py')
    sales = [collections.defaultdict(lambda: {'units': 0, 'revenue': 0}) for _ in range(2)]
    costs = [collections.Counter() for _ in range(2)]
    snapshots = []
    timing = []
    original_commit = K._commit_unit
    original_process = K._process_market
    identities = {}

    def process(state, env):
        identities.clear()
        identities.update({id(f): i for i, f in enumerate(state[0].observation.farms)})
        return original_process(state, env)

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = original_commit(op, item, price, farm, private, market, shed_capacity)
        if ok:
            player = identities[id(farm)]
            if op == 'SELL':
                sales[player][item]['units'] += 1
                sales[player][item]['revenue'] += price
            else:
                costs[player][op] += price
        return ok

    def tracked(obs, config=None):
        start = time.perf_counter()
        action = mod.agent(obs, config)
        timing.append(time.perf_counter() - start)
        if obs['step'] % 24 == 0:
            counts = collections.Counter()
            for row in obs['farms'][0]['tiles']:
                for tile in row:
                    if isinstance(tile, dict):
                        if tile.get('crop'): counts[tile['crop']] += 1
                        if tile.get('animal'): counts[tile['animal']] += 1
            snapshots.append({'day': obs['step'] // 24, 'shops': list(obs['town']['unlocked_shops']),
                              'farm': dict(counts), 'money': obs['farms'][0]['money'],
                              'route': mod._IMPL.chassis.players.get(0, {}).get('route')})
        return action

    K._commit_unit = commit
    K._process_market = process
    try:
        env = make('kaggriculture', debug=True, configuration={'seed': seed})
        env.run([tracked, rival.agent])
    finally:
        K._commit_unit = original_commit
        K._process_market = original_process
    assert [x.status for x in env.steps[-1]] == ['DONE', 'DONE']
    report = {k: v for k, v in vars(mod).items() if k.endswith('_REPORT') and isinstance(v, dict)}
    data = {'source': str(SOURCE), 'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'seed': seed, 'seat': 0, 'opponent': 'tape_a2 (older local opponent, not a current top-10 agent)',
            'scores': [x.reward for x in env.steps[-1]], 'sales': sales, 'purchases_excluding_hires_land': costs,
            'route_count': len(mod._IMPL.chassis.routes), 'snapshots': snapshots, 'telemetry': report,
            'mean_seconds': sum(timing) / len(timing), 'max_seconds': max(timing)}
    target = Path(__file__).with_name('received_v8_probe_' + str(seed) + '.json')
    target.write_text(json.dumps(data, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in data.items() if k not in ('snapshots', 'telemetry')}, default=dict), flush=True)
    print(json.dumps({'telemetry': {k: v for k, v in report.items() if any(v.values())}}, default=dict), flush=True)


if __name__ == '__main__':
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 210001)
