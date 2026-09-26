"""Per-day, per-product cash flows of both seats in recorded games (both tapes replayed).
usage: day_fills.py games.json id1,id2,... [from_day] [team]"""
import sys, os, json, collections
sys.argv = [sys.argv[0]] + [os.path.abspath(a) if a.endswith('.json') else a for a in sys.argv[1:]]
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena')); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
os.chdir(HERE)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
from pinned4 import _tape
games = {str(g['id']): g for g in json.load(open(sys.argv[1]))}
ids = sys.argv[2].split(','); d0 = int(sys.argv[3]) if len(sys.argv) > 3 else 24
team = sys.argv[4] if len(sys.argv) > 4 else 'offhand'
for gid in ids:
    d = games[gid]; P = d['info']['TeamNames'].index(team); O = 1 - P
    FARMS = [None, None]; STEP = [0]; log = []; MONEY = {}; INV = {}
    oc, opm, oh = K._commit_unit, K._process_market, K._do_hire
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            log.append((STEP[0], 0 if farm is FARMS[0] else 1, op, item, price))
        return ok
    def pm(state, env):
        st = state[0].observation.step
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = st
        if st % 24 == 0:
            MONEY[st // 24] = [round(state[0].observation.farms[i]['money']) for i in (0, 1)]
            INV[st // 24] = [dict(state[i].observation.private['shed']) for i in (0, 1)]
        return opm(state, env)
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None and farm['money'] < m0:
            log.append((STEP[0], 0 if farm is FARMS[0] else 1, 'HIRE', '-', m0 - farm['money']))
    K._commit_unit, K._process_market, K._do_hire = commit, pm, hire
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[_tape(d['acts'], 0), _tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._process_market, K._do_hire = oc, opm, oh
    print('=' * 110)
    print('game', gid, 'us', d['info']['TeamNames'][P], r['r'][P], 'vs', d['info']['TeamNames'][O], r['r'][O], 'margin', r['r'][P] - r['r'][O])
    for day in range(d0, 30):
        rows = collections.defaultdict(lambda: [0.0, 0.0, 0, 0])
        for st, pl, op, item, price in log:
            if st // 24 != day: continue
            key = ('S:' if op == 'SELL' else ('B:' if op.startswith('BUY') else 'H:')) + item[:5]
            i = 0 if pl == P else 1
            sgn = 1 if op == 'SELL' else -1
            rows[key][i] += sgn * price; rows[key][2 + i] += 1
        m = MONEY.get(day, [0, 0])
        tot = [sum(v[0] for v in rows.values()), sum(v[1] for v in rows.values())]
        print('day %d start cash us %d them %d (lead %+d) | day net us %+d them %+d (diff %+d)' % (day, m[P], m[O], m[P] - m[O], tot[0], tot[1], tot[0] - tot[1]))
        sh = INV.get(day, [{}, {}])
        print('   shed us', {k: v for k, v in sorted(sh[P].items()) if v}, '| them', {k: v for k, v in sorted(sh[O].items()) if v})
        print('   ' + '  '.join('%s %+d/%+d (%d/%d)' % (k, v[0], v[1], v[2], v[3]) for k, v in sorted(rows.items()) if abs(v[0]) + abs(v[1]) >= 20))
