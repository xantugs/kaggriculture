"""Revenue/cost ledger per product for both seats of recorded offhand games vs given teams (tape replay, real seed).
usage: topledger.py team1,team2,...  -> mean (them - us) per ledger key, plus final cash"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, pinned
from kaggle_environments.envs.kaggriculture import kaggriculture as K
FILES = ['loss_0922b.json', 'loss_0922c.json', 'v10v11_top_0922.json', 'v12_all_0922.json', 'strong_new.json', 'recent_loss.json',
         'v1011_losses_b.json', 'strong_v9.json']
teams = sys.argv[1].split(',')
games = {}
for f in FILES:
    for d in json.load(open(os.path.join(HERE, f), encoding='utf-8')):
        n = d['info'].get('TeamNames') or []
        if 'offhand' in n and n[1 - n.index('offhand')] in teams:
            games[d['id']] = d
tot = collections.Counter(); cnt = 0
for d in games.values():
    n = d['info']['TeamNames']; P = n.index('offhand'); O = 1 - P
    led = [collections.Counter(), collections.Counter()]; FARMS = [None, None]
    oc, oh, opm = K._commit_unit, K._do_hire, K._process_market
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        k = 0 if farm is FARMS[0] else 1
        if ok and op == 'SELL': led[k][item] += price
        elif ok and op == 'BUY_PRODUCT': led[k]['buy_' + item] -= price
        elif ok and op == 'BUY_SEED': led[k]['seed'] -= price
        elif ok and op == 'BUY_ANIMAL': led[k]['anim'] -= price
        elif ok: led[k][op.lower()] -= price
        return ok
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult); led[0 if farm is FARMS[0] else 1]['hire'] += farm['money'] - m0
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    K._commit_unit, K._do_hire, K._process_market = commit, hire, pm
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._do_hire, K._process_market = oc, oh, opm
    ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
    if not ok:
        print('replay mismatch', d['id']); continue
    cnt += 1
    for k in set(led[0]) | set(led[1]):
        tot[k] += led[O][k] - led[P][k]
    tot['CASH'] += d['rewards'][O] - d['rewards'][P]
print('games', cnt, 'of', len(games))
for k, v in sorted(tot.items(), key=lambda kv: -abs(kv[1])):
    print(f"  {k:18s} them-us {v / max(1, cnt):+9.0f}")
