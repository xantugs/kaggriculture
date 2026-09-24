"""When/at what price top teams buy and sell WHEAT (and TOMATO) vs us in recorded games. usage: wheattrade.py teams item"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K
from topledger import FILES
teams, ITEM = sys.argv[1].split(','), sys.argv[2]
games = {}
for f in FILES:
    for d in json.load(open(os.path.join(HERE, f), encoding='utf-8')):
        n = d['info'].get('TeamNames') or []
        if 'offhand' in n and n[1 - n.index('offhand')] in teams:
            games[d['id']] = d
agg = {s: collections.defaultdict(lambda: [0, 0, 0, 0]) for s in ('us', 'them')}   # day -> [buy units, buy $, sell units, sell $]
for d in games.values():
    n = d['info']['TeamNames']; P = n.index('offhand'); FARMS = [None, None]; STEP = [0]
    oc, opm = K._commit_unit, K._process_market
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and item == ITEM and op in ('BUY_PRODUCT', 'SELL'):
            who = 'us' if (farm is FARMS[P]) else 'them'; a = agg[who][STEP[0] // 24]
            if op == 'BUY_PRODUCT': a[0] += 1; a[1] += price
            else: a[2] += 1; a[3] += price
        return ok
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]; STEP[0] = state[0].observation.step
        return opm(state, env)
    K._commit_unit, K._process_market = commit, pm
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._process_market = oc, opm
g = len(games); print('games', g, ITEM, 'per game: units bought@avg / sold@avg')
for day in range(30):
    row = []
    for s in ('us', 'them'):
        b, bp, sl, sp = agg[s][day]
        row.append(f"{s} buy {b/g:5.1f}@{bp/max(b,1):5.1f} sell {sl/g:5.1f}@{sp/max(sl,1):5.1f}")
    if any(agg[s][day][0] or agg[s][day][2] for s in agg): print(f"day {day:2d}  " + '   '.join(row))
