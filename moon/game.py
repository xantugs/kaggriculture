"""One decoupled closed-loop game with a per-product sales ledger. usage: game.py A B seed"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
led = [{}, {}]
orig = K._commit_unit
cur = {'p': None}
def commit(op, item, price, farm, private, market, cap=100):
    ok = orig(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL':
        i = 0 if farm is FARMS[0] else 1
        d = led[i].setdefault(item, [0, 0]); d[0] += 1; d[1] += price
    return ok
K._commit_unit = commit
FARMS = [None, None]
orig_pm = K._process_market
def pm(state, env):
    FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
    return orig_pm(state, env)
K._process_market = pm
t = time.time()
r = lean.play(None, None, seed, agent_objs=[A, B], record=True)
print(json.dumps({k: r[k] for k in ('r', 'st', 'err', 'tmax', 'shops')}))
print('wall', round(time.time() - t, 1))
for i in range(2):
    print('seat', i, {k: (v[0], v[1]) for k, v in sorted(led[i].items())})
tel = getattr(A, 'telemetry', None)
if tel: print('telemetry', tel)
fo = r['final_obs']
for i in range(2):
    f = fo['farms'][i]
    print('seat', i, 'money', f['money'], 'quads', f['unlocked_quadrants'])
    for row in f['tiles']:
        print(' ', ' '.join('#' if t == 'LOCKED' else '.' if t is None else (t.get('crop') or t.get('animal') or t['kind'])[:2] for t in row))
