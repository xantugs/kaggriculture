"""Units harvested per product and per day for us (candidate from step S) and the rival, prefix replay in the real town."""
import sys, json, collections, lean, ident2, pfx
from kaggle_environments.envs.kaggriculture import kaggriculture as K
f, gi, cand, S = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]); item = sys.argv[5]
d = json.load(open(f))[gi]; names = d['info']['TeamNames']; P = names.index('Khantugs Gantulga')
cur = {'s': 0}; got = collections.defaultdict(lambda: [0, 0])
oa = K._apply_unit_action
def apply(farm, private, idx, action, board_size, day, tpd, cap=100):
    before = sum(int(i.get(item, 0)) for i in private['inventories'])
    r = oa(farm, private, idx, action, board_size, day, tpd, cap)
    after = sum(int(i.get(item, 0)) for i in private['inventories'])
    if isinstance(action, list) and action and action[0] == 'HARVEST' and after > before:
        pl = cur['map'].get(id(farm))
        if pl is not None: got[day][0 if pl == P else 1] += after - before
    return r
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms: cur['map'] = {id(o.farms[0]): 0, id(o.farms[1]): 1}
    return oi(state, env)
K._apply_unit_action = apply; K.interpreter = interp
A = lean.load(cand)
ag = [ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)]; ag[P] = pfx.prefixed(A, d['acts'], P, S)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
tu = sum(v[0] for v in got.values()); tt = sum(v[1] for v in got.values())
print(names[1 - P], 'margin', r['r'][P] - r['r'][1 - P], item, 'harvested us', tu, 'them', tt)
print({dd: tuple(v) for dd, v in sorted(got.items()) if v[0] != v[1]})
