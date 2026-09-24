"""Where do goods vanish? harvested units, night-drop overflow, decay losses, final unsold. usage: leaks.py A B seed"""
import sys, os, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
FARMS = [None, None]; PRIV = [None, None]; OVL = []; STEPX = [0]
H = [collections.Counter(), collections.Counter()]; OVF = [collections.Counter(), collections.Counter()]
DEC = [collections.Counter(), collections.Counter()]; SOLD = [collections.Counter(), collections.Counter()]
oa = K._apply_unit_action
def apply(farm, private, idx, action, bs, day, tpd, cap=100):
    i = 0 if farm is FARMS[0] else 1
    inv = K._farmer_inventory(private, idx); before = dict(inv)
    oa(farm, private, idx, action, bs, day, tpd, cap)
    if isinstance(action, list) and action and action[0] == 'HARVEST':
        for k, v in inv.items():
            if v > before.get(k, 0): H[i][k] += v - before.get(k, 0)
K._apply_unit_action = apply
od = K._drop_inventories_to_shed
def drop(private, capacity):
    i = 0 if private is PRIV[0] else 1
    carried = collections.Counter()
    for inv in private['inventories']:
        for k, v in inv.items(): carried[k] += v
    before = dict(private['shed'])
    od(private, capacity)
    for k, v in carried.items():
        got = private['shed'].get(k, 0) - before.get(k, 0)
        if got < v:
            OVF[i][k] += v - got
            if i == 0: OVL.append((STEPX[0] // 24, k, v - got, sum(before.values()), dict(carried)))
K._drop_inventories_to_shed = drop
odp = K._decay_plants
def decay(farm, step):
    i = 0 if farm is FARMS[0] else 1
    b = {(x, y): t.get('yield_units', 0) for y, row in enumerate(farm['tiles']) for x, t in enumerate(row) if isinstance(t, dict) and t.get('kind') == 'PLANT'}
    odp(farm, step)
    for (x, y), yu in b.items():
        t = farm['tiles'][y][x]
        now = t.get('yield_units', 0) if isinstance(t, dict) and t.get('kind') == 'PLANT' else 0
        if now < yu:
            crop = [c for c in ['x']][0]
            DEC[i][(t.get('crop') if isinstance(t, dict) and t.get('crop') else 'gone')] += yu - max(0, now)
K._decay_plants = decay
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL': SOLD[0 if farm is FARMS[0] else 1][item] += 1
    return ok
K._commit_unit = commit
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms:
        FARMS[0], FARMS[1] = o.farms[0], o.farms[1]; STEPX[0] = o.get("step", 0)
        PRIV[0], PRIV[1] = state[0].observation.private, state[1].observation.private
    return oi(state, env)
K.interpreter = interp
r = lean.play(None, None, seed, agent_objs=[A, B], record=True)
print('result', r['r'])
for i in range(2):
    print('seat', i, 'harvested', dict(H[i])); print('   overflow', dict(OVF[i]), 'decayed', dict(DEC[i])); print('   sold', dict(SOLD[i]), 'final shed', {k: v for k, v in r['final_obs']['farms'][i].items() if False})
for e in OVL: print(e)
