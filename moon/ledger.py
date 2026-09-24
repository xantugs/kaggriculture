"""Daily cash ledger per seat from day D0: sales by product, buys, hires. usage: ledger.py A B seed D0 D1"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D0, D1 = int(sys.argv[4]), int(sys.argv[5])
FARMS = [None, None]; STEP = [0]
L = collections.defaultdict(float)
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok:
        i = 0 if farm is FARMS[0] else 1
        key = ('+' + item[:5]) if op == 'SELL' else ('-' + op[4:7] + item[:4])
        L[(i, key)] += price if op == 'SELL' else -price
    return ok
K._commit_unit = commit
oh = K._do_hire
def hire(farm, private, bs, mult=1):
    m0 = farm['money']; oh(farm, private, bs, mult)
    L[(0 if farm is FARMS[0] else 1, '-HIRE')] += farm['money'] - m0
K._do_hire = hire
ol = K._do_buy_land
def land(farm, bs):
    m0 = farm['money']; ol(farm, bs)
    L[(0 if farm is FARMS[0] else 1, '-LAND')] += farm['money'] - m0
K._do_buy_land = land
opm = K._process_market
def pm(state, env):
    FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
    s = state[0].observation.step
    if D0 * 24 <= s < (D1 + 1) * 24: return opm(state, env)
    saved = dict(L); r = opm(state, env); L.clear(); L.update(saved); return r
K._process_market = pm
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'], 'days', D0, D1)
keys = sorted(set(k for _, k in L))
for k in keys:
    a, b = L.get((0, k), 0), L.get((1, k), 0)
    print(f"{k:10s} {a:9.0f} {b:9.0f} {a-b:+9.0f}")
print(f"{'NET':10s} {sum(v for (i,_),v in L.items() if i==0):9.0f} {sum(v for (i,_),v in L.items() if i==1):9.0f}")
