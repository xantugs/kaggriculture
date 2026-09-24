"""One pinned game, daily detail for our seat: animals/crops, and per-product sales. usage: pin1.py games.json gid cand [prods]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import pinned, lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
f, gid, cand = sys.argv[1], int(sys.argv[2]), sys.argv[3]
prods = sys.argv[4].split(',') if len(sys.argv) > 4 else ['WOOL', 'MILK', 'STRAWBERRY', 'WHEAT']
games = json.load(open(f, encoding='utf-8'))
d = [g for g in games if g['id'] == gid][0]
names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
spawns, shops, _ = pinned.reference(d)
pinned.install_pinned(15, O, spawns, shops)
S = 360
FARMS = [None, None]; STEP = [0]; led = collections.defaultdict(lambda: [0, 0]); daily = []
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL' and FARMS[0] is not None:
        i = 0 if farm is FARMS[0] else 1
        e = led[(STEP[0] // 24, i, item)]; e[0] += 1; e[1] += price
    return ok
K._commit_unit = commit
opm = K._process_market
def pm(state, env):
    FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]; STEP[0] = state[0].observation.step
    if STEP[0] % 24 == 23 and STEP[0] >= S - 24:
        c = collections.Counter()
        for row in FARMS[P]['tiles']:
            for t in row:
                if isinstance(t, dict): c[t.get('animal') or t.get('crop') or t['kind']] += 1
        daily.append((STEP[0] // 24, int(FARMS[P]['money']), dict(c), {k: v for k, v in state[P].observation.private['shed'].items() if v}))
    return opm(state, env)
K._process_market = pm
A = lean.load(cand)
ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
print('result us', r['r'][P], 'them', r['r'][O], 'opp', names[O], 'shops', shops)
for e in daily: print(e)
for day in range(15, 30):
    row = []
    for it in prods:
        a = led.get((day, P, it)); b = led.get((day, O, it))
        if a or b: row.append(f"{it[:4]} {(str(a[0])+'@'+str(a[1]//a[0])) if a else '-'}|{(str(b[0])+'@'+str(b[1]//b[0])) if b else '-'}")
    print(day, '  '.join(row))
print('telemetry', {k: v for k, v in A.telemetry.items() if k != 'log'})
