"""Harvest/sold/overflow for our seat in one pinned game. usage: pinleak.py games.json gid cand"""
import sys, json, collections
sys.path.insert(0, '.'); sys.path.insert(0, '../arena')
import pinned, lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
f, gid, cand = sys.argv[1], int(sys.argv[2]), sys.argv[3]
d = [g for g in json.load(open(f, encoding='utf-8')) if g['id'] == gid][0]
P = d['info']['TeamNames'].index('offhand'); O = 1 - P
sp, sh, _ = pinned.reference(d); pinned.install_pinned(15, O, sp, sh)
FARMS = [None, None]; PRIV = [None, None]; STEP = [0]
H = collections.Counter(); OVF = collections.Counter(); SOLD = collections.Counter(); OVD = collections.Counter()
oa = K._apply_unit_action
def apply(farm, private, idx, action, bs, day, tpd, cap=100):
    inv = K._farmer_inventory(private, idx); b = dict(inv)
    oa(farm, private, idx, action, bs, day, tpd, cap)
    if farm is FARMS[P] and STEP[0] >= 360 and isinstance(action, list) and action and action[0] == 'HARVEST':
        for k, v in inv.items():
            if v > b.get(k, 0): H[k] += v - b.get(k, 0)
K._apply_unit_action = apply
od = K._drop_inventories_to_shed
def drop(private, capacity):
    if private is PRIV[P] and STEP[0] >= 360:
        car = collections.Counter()
        for inv in private['inventories']:
            for k, v in inv.items(): car[k] += v
        b = dict(private['shed']); od(private, capacity)
        for k, v in car.items():
            got = private['shed'].get(k, 0) - b.get(k, 0)
            if got < v: OVF[k] += v - got; OVD[STEP[0] // 24] += v - got
        return
    return od(private, capacity)
K._drop_inventories_to_shed = drop
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL' and farm is FARMS[P] and STEP[0] >= 360: SOLD[item] += 1
    return ok
K._commit_unit = commit
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms:
        FARMS[0], FARMS[1] = o.farms[0], o.farms[1]; PRIV[0], PRIV[1] = state[0].observation.private, state[1].observation.private; STEP[0] = o.get('step', 0)
    return oi(state, env)
K.interpreter = interp
A = lean.load(cand)
ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, 360); ag[O] = pinned._tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
print('us', r['r'][P], 'them', r['r'][O])
print('harvested', dict(H)); print('sold', dict(SOLD)); print('overflow', dict(OVF), 'by day', dict(OVD))
