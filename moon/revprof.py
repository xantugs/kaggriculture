"""Absolute per-product revenue/costs per game for one team (tape replay of recorded games, real seed), sampled.
usage: revprof.py team max_games file..."""
import sys, os, json, collections, random
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(d):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    n = d['info']['TeamNames']; P = n.index(d['_team'])
    led = [collections.Counter(), collections.Counter()]; FARMS = [None, None]
    oc, oh, opm = K._commit_unit, K._do_hire, K._process_market
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        k = 0 if farm is FARMS[0] else 1
        if ok and op == 'SELL': led[k][item] += price; led[k]['n_' + item] += 1
        elif ok and op == 'BUY_PRODUCT': led[k]['buy_' + item] -= price
        elif ok and op == 'BUY_SEED': led[k]['seeds'] -= price
        elif ok and op == 'BUY_ANIMAL': led[k]['animals'] -= price
        elif ok and op == 'BUY_LAND': led[k]['land'] -= price
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
    return ok, dict(led[P]), dict(led[1 - P]), d['rewards'][P], d['rewards'][1 - P]
if __name__ == '__main__':
    team, mx, files = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    gs = []
    for f in files:
        it = (json.loads(l) for l in open(f, encoding='utf-8')) if f.endswith('.jsonl') else json.load(open(f, encoding='utf-8'))
        for d in it:
            nm = d["info"].get("TeamNames") or []
            if team in nm and (not os.environ.get("OPPS") or nm[1 - nm.index(team)] in os.environ["OPPS"].split("|")): d["_team"] = team; gs.append(d)
    random.Random(0).shuffle(gs); gs = gs[:mx]
    tot = [collections.Counter(), collections.Counter()]; c = 0; cash = [0, 0]
    with ProcessPoolExecutor(8) as ex:
        for ok, a, b, ra, rb in ex.map(job, gs):
            if not ok: continue
            c += 1; tot[0].update(a); tot[1].update(b); cash[0] += ra; cash[1] += rb
    print(f"{team}: {c} games replayed; cash {cash[0]/c:.0f} vs opp {cash[1]/c:.0f}")
    keys = ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER','buy_WHEAT','buy_FERTILIZER','seeds','animals','land','hire']
    for k in keys:
        n = tot[0].get('n_' + k, 0) / c
        print(f"  {k:15s} {team[:8]} {tot[0].get(k,0)/c:+9.0f}" + (f" ({n:5.0f} u @{tot[0].get(k,0)/max(1,tot[0].get('n_'+k,0)):4.0f})" if n else ' ' * 18) + f"   opp {tot[1].get(k,0)/c:+9.0f}")
