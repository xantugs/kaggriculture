"""Premium sale timing vs the rival in recorded games: per day and product, units, $ and mean sale hour of both.
usage: prem_timing.py games.json id1,id2 [from_day] [products]"""
import sys, os, json, collections
sys.argv = [sys.argv[0]] + [os.path.abspath(a) if a.endswith('.json') else a for a in sys.argv[1:]]
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena')); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
os.chdir(HERE)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
from pinned4 import _tape
games = {str(g['id']): g for g in json.load(open(sys.argv[1]))}
ids = sys.argv[2].split(','); d0 = int(sys.argv[3]) if len(sys.argv) > 3 else 12
prods = sys.argv[4].split(',') if len(sys.argv) > 4 else ['WOOL', 'STRAWBERRY', 'MILK']
TOT = collections.defaultdict(lambda: [0, 0, 0.0, 0.0])
for gid in ids:
    d = games[gid]; P = d['info']['TeamNames'].index('offhand')
    F = [None, None]; ST = [0]; L = []
    oc, opm = K._commit_unit, K._process_market
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and op == 'SELL' and item in prods and F[0] is not None:
            L.append((ST[0], 0 if farm is F[P] else 1, item, price))
        return ok
    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]; ST[0] = state[0].observation.step
        return opm(state, env)
    K._commit_unit, K._process_market = commit, pm
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[_tape(d['acts'], 0), _tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._process_market = oc, opm
    print('== game', gid, d['info']['TeamNames'][1 - P], 'margin', r['r'][P] - r['r'][1 - P])
    agg = collections.defaultdict(lambda: [[0, 0.0, 0.0], [0, 0.0, 0.0]])
    for st, i, item, px in L:
        if st // 24 < d0: continue
        a = agg[(st // 24, item)][i]; a[0] += 1; a[1] += px; a[2] += st % 24
    for (day, item), (u, t) in sorted(agg.items()):
        diff = u[1] - t[1]
        TOT[item][0] += u[0]; TOT[item][1] += t[0]; TOT[item][2] += u[1]; TOT[item][3] += t[1]
        if abs(diff) >= 150:
            print('  d%02d %-10s us %3d $%6.0f h%4.1f | them %3d $%6.0f h%4.1f | diff %+6.0f' % (day, item, u[0], u[1], u[2] / max(1, u[0]), t[0], t[1], t[2] / max(1, t[0]), diff))
print('TOTAL from day %d:' % d0, {k: (v[0], v[1], round(v[2]), round(v[3]), round(v[2] - v[3])) for k, v in TOT.items()})
