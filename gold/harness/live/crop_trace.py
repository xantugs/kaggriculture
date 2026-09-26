"""Hourly trace of one crop on both farms of a recorded game: plants, units on tiles, units in shed, sales.
usage: crop_trace.py games.json gid CROP from_day [team]"""
import sys, os, json, collections
sys.argv = [sys.argv[0]] + [os.path.abspath(a) if a.endswith('.json') else a for a in sys.argv[1:]]
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena')); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
os.chdir(HERE)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
from pinned4 import _tape
g = [x for x in json.load(open(sys.argv[1])) if str(x['id']) == sys.argv[2]][0]
crop = sys.argv[3]; d0 = int(sys.argv[4]); team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
P = g['info']['TeamNames'].index(team); O = 1 - P
PROD = {'COW': 'MILK', 'SHEEP': 'WOOL', 'GOOSE': 'EGG'}
sold = collections.Counter(); FARMS = [None, None]; STEP = [0]; OUT = []
oc, opm = K._commit_unit, K._process_market
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL' and item == crop and FARMS[0] is not None:
        sold[(STEP[0], 0 if farm is FARMS[P] else 1)] += 1
    return ok
def farm_stat(farm):
    n = u = w = 0
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict):
                c = t.get('crop') or PROD.get(t.get('animal'))
                if c == crop:
                    n += 1; u += int(t.get('yield_units', 0) or 0)
                if t.get('kind') == 'WEED': w += 1
    return n, u, w
def pm(state, env):
    st = state[0].observation.step
    FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
    STEP[0] = st
    if st >= d0 * 24:
        a = farm_stat(state[0].observation.farms[P]); b = farm_stat(state[0].observation.farms[O])
        sa = int(state[P].observation.private['shed'].get(crop, 0)); sb = int(state[O].observation.private['shed'].get(crop, 0))
        ca = sum(int(inv.get(crop, 0)) for inv in state[P].observation.private['inventories'])
        cb = sum(int(inv.get(crop, 0)) for inv in state[O].observation.private['inventories'])
        px = state[0].observation.market['prices'].get(crop)
        OUT.append('d%02d h%02d px %4s | us plants %2d on-tiles %3d carried %3d shed %3d weeds %2d | them plants %2d on-tiles %3d carried %3d shed %3d weeds %2d' % (
            st // 24, st % 24, px, a[0], a[1], ca, sa, a[2], b[0], b[1], cb, sb, b[2]))
    r = opm(state, env)
    return r
K._commit_unit, K._process_market = commit, pm
r = lean.play(None, None, g['info']['seed'], agent_objs=[_tape(g['acts'], 0), _tape(g['acts'], 1)])
print(chr(10).join(OUT))
tot = collections.Counter()
for (st, i), n in sorted(sold.items()):
    tot[i] += n
print('sold', crop, 'us', tot[0], 'them', tot[1], 'by step:', [(st, i, n) for (st, i), n in sorted(sold.items()) if st >= d0 * 24])
