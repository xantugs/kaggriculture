import sys, json, collections, lean, ident2
from kaggle_environments.envs.kaggriculture import kaggriculture as K
f, item = sys.argv[1], sys.argv[2]
lo = int(sys.argv[3]) if len(sys.argv) > 3 else 0; hi = int(sys.argv[4]) if len(sys.argv) > 4 else 720
fn, _, gi = f.partition(":"); d = json.load(open(fn))[int(gi or 0)]
names = d['info']['TeamNames']; us = names.index(sys.argv[5]) if len(sys.argv) > 5 else names.index('Khantugs Gantulga'); them = 1 - us
cur = {'s': 0}; farms = {}; ev = collections.defaultdict(lambda: [[], []]); animals = {}
oc = K._commit_unit
def commit(op, it, price, farm, private, market, cap=100):
    ok = oc(op, it, price, farm, private, market, cap)
    p = farms.get(id(farm), -1)
    if ok and p >= 0 and it == item and lo <= cur['s'] < hi:
        ev[cur['s']][p].append(price if op == 'SELL' else -price)
    return ok
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms:
        farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1
        cur['s'] = o.get('step', 0)
        if cur['s'] % 24 == 12:
            animals[cur['s'] // 24] = [collections.Counter(t.get('animal') for row in fm['tiles'] for t in row if isinstance(t, dict) and t.get('animal')) for fm in o.farms]
    return oi(state, env)
K._commit_unit = commit; K.interpreter = interp
lean.play(None, None, d['info']['seed'], agent_objs=[ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)])
tot = [[0, 0], [0, 0]]
for s in sorted(ev):
    a, b = ev[s][us], ev[s][them]
    for p, lst in ((0, a), (1, b)):
        tot[p][0] += len(lst); tot[p][1] += sum(lst)
    print(f"step {s:3d} d{s//24:2d}h{s%24:02d}  us {len(a):3d}u {('@'+str(a[0])+'..'+str(a[-1])) if a else '':14s}  them {len(b):3d}u {('@'+str(b[0])+'..'+str(b[-1])) if b else ''}")
print('totals us', tot[0], 'them', tot[1])
print('animals by day (us | them):', {dd: (dict(animals[dd][us]), dict(animals[dd][them])) for dd in (8, 12, 16, 20, 24) if dd in animals})
