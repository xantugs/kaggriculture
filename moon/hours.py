"""Sale hour profile per product per seat (days D0..D1): units and avg price by hour. usage: hours.py A B seed D0 D1 PROD"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D0, D1 = int(sys.argv[4]), int(sys.argv[5]); P = sys.argv[6]
FARMS = [None, None]; STEP = [0]; H = [collections.defaultdict(lambda: [0, 0]), collections.defaultdict(lambda: [0, 0])]
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL' and item == P and D0 * 24 <= STEP[0] < (D1 + 1) * 24:
        d = H[0 if farm is FARMS[0] else 1][STEP[0] % 24]; d[0] += 1; d[1] += price
    return ok
K._commit_unit = commit
opm = K._process_market
def pm(state, env):
    FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]; STEP[0] = state[0].observation.step
    return opm(state, env)
K._process_market = pm
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'], P)
for h in range(24):
    a, b = H[0].get(h), H[1].get(h)
    if a or b: print(f"h{h:02d}  {(str(a[0])+'@'+str(a[1]//a[0])) if a else '-':>10} {(str(b[0])+'@'+str(b[1]//b[0])) if b else '-':>10}")
for i in range(2):
    u = sum(v[0] for v in H[i].values()); m = sum(v[1] for v in H[i].values()); print('seat', i, u, 'units avg', m // max(1, u))
