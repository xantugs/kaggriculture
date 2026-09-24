"""Daily sales per product for both seats: units@avgprice. usage: sales.py A B seed [products]"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
prods = sys.argv[4].split(',') if len(sys.argv) > 4 else None
FARMS = [None, None]; STEP = [0]
led = collections.defaultdict(lambda: [0, 0])
orig_c = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = orig_c(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL':
        i = 0 if farm is FARMS[0] else 1
        d = led[(STEP[0] // 24, i, item)]; d[0] += 1; d[1] += price
    return ok
K._commit_unit = commit
orig_pm = K._process_market
def pm(state, env):
    FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
    STEP[0] = state[0].observation.step
    return orig_pm(state, env)
K._process_market = pm
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'], r['shops'])
items = prods or sorted(set(k[2] for k in led))
for d in range(30):
    row = []
    for it in items:
        a = led.get((d, 0, it)); b = led.get((d, 1, it))
        if a or b:
            fa = f"{a[0]}@{a[1]//max(1,a[0])}" if a else '-'
            fb = f"{b[0]}@{b[1]//max(1,b[0])}" if b else '-'
            row.append(f"{it[:4]} {fa}|{fb}")
    if row: print(d, '  '.join(row))
