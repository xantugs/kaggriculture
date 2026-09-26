"""Endgame aggregate over recorded games: per game, both seats' seeds bought by crop on days 22-28 and sales by
product (units, $) on days 24-29 per day. usage: endgame_agg.py games.json ids_file out.jsonl [team]"""
import sys, os, json, collections
sys.argv = [sys.argv[0]] + [os.path.abspath(a) if ('.' in a and '/' in a or a.endswith(('.json', '.jsonl', '.txt'))) else a for a in sys.argv[1:]]
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena')); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
os.chdir(HERE)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
from pinned4 import _tape
games = {str(g['id']): g for g in json.load(open(sys.argv[1]))}
ids = open(sys.argv[2]).read().split(); out = open(sys.argv[3], 'w')
team = sys.argv[4] if len(sys.argv) > 4 else 'offhand'
for gid in ids:
    d = games[gid]; P = d['info']['TeamNames'].index(team); O = 1 - P
    FARMS = [None, None]; STEP = [0]; led = collections.defaultdict(float); cnt = collections.defaultdict(int); MONEY = {}; HIRES = collections.defaultdict(int)
    oc, opm, oh = K._commit_unit, K._process_market, K._do_hire
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 'us' if (farm is FARMS[P]) else 'them'
            key = (i, STEP[0] // 24, op, item)
            led[key] += price; cnt[key] += 1
        return ok
    def pm(state, env):
        st = state[0].observation.step
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = st
        if st % 24 == 0:
            MONEY[st // 24] = [round(state[0].observation.farms[i]['money']) for i in (P, O)]
        return opm(state, env)
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None and farm['money'] < m0:
            i = 'us' if (farm is FARMS[P]) else 'them'
            HIRES[(i, STEP[0] // 24)] += 1; led[(i, STEP[0] // 24, 'HIRE', '-')] += m0 - farm['money']
    K._commit_unit, K._process_market, K._do_hire = commit, pm, hire
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[_tape(d['acts'], 0), _tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._process_market, K._do_hire = oc, opm, oh
    rows = [[k[0], k[1], k[2], k[3], cnt[k], round(v)] for k, v in led.items() if k[1] >= 20]
    out.write(json.dumps(dict(id=gid, P=P, opp=d['info']['TeamNames'][O], r=[r['r'][P], r['r'][O]], money=MONEY,
                              hires={'%s:%d' % k: v for k, v in HIRES.items()}, rows=rows)) + '\n')
    out.flush()
    print(gid, r['r'][P] - r['r'][O], flush=True)
