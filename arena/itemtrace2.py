"""itemtrace for a candidate playing our seat from step S (prefix replay, real town)."""
import sys, json, collections, lean, ident2, pfx
from kaggle_environments.envs.kaggriculture import kaggriculture as K
f, gi, item, cand, S = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], int(sys.argv[5])
lo = int(sys.argv[6]) if len(sys.argv) > 6 else 0
d = json.load(open(f))[gi]; names = d['info']['TeamNames']; us = names.index('Khantugs Gantulga'); them = 1 - us
cur = {'s': 0}; farms = {}; ev = collections.defaultdict(lambda: [[], []]); held = {}
oc = K._commit_unit
def commit(op, it, price, farm, private, market, cap=100):
    ok = oc(op, it, price, farm, private, market, cap)
    p = farms.get(id(farm), -1)
    if ok and p >= 0 and it == item and cur['s'] >= lo:
        ev[cur['s']][p].append(price if op == 'SELL' else -price)
    return ok
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms:
        farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1; cur['s'] = o.get('step', 0)
        held[cur['s']] = [int(state[i].observation.private['shed'].get(item, 0)) for i in (0, 1)]
    return oi(state, env)
K._commit_unit = commit; K.interpreter = interp
A = lean.load(cand)
ag = [ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)]; ag[us] = pfx.prefixed(A, d['acts'], us, S)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
tot = [[0, 0], [0, 0]]
for s in sorted(ev):
    a, b = ev[s][us], ev[s][them]
    for p, lst in ((0, a), (1, b)):
        tot[p][0] += len(lst); tot[p][1] += sum(lst)
    h = held.get(s, [0, 0])
    print(f"step {s:3d} d{s//24:2d}h{s%24:02d}  us {len(a):3d}u {('@'+str(a[0])+'..'+str(a[-1])) if a else '':14s} shed {h[us]:3d} | them {len(b):3d}u {('@'+str(b[0])+'..'+str(b[-1])) if b else '':14s} shed {h[them]:3d}")
print('totals us', tot[0], 'them', tot[1], 'margin', r['r'][us] - r['r'][them])
