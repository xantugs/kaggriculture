"""Per-day sales (units, revenue) per product per side for recorded games, split copy/divergent by first-144-step
action similarity. usage: timing_anatomy.py games.json out.jsonl [team=offhand]"""
import sys, json, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena')

def one(d):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    acts = d['acts']; FARMS = [None, None]; STEP = [0]
    sales = [collections.defaultdict(lambda: [0, 0.0]) for _ in range(2)]   # (day, product) -> [units, revenue]
    buys = [collections.defaultdict(lambda: [0, 0.0]) for _ in range(2)]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            day = STEP[0] // 24
            if op == 'SELL':
                sales[i][(day, item)][0] += 1; sales[i][(day, item)][1] += price
            elif op == 'BUY_PRODUCT':
                buys[i][(day, item)][0] += 1; buys[i][(day, item)][1] += price
        return ok
    opm = K._process_market
    def pm(state, env):
        STEP[0] = state[0].observation.step
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    K._commit_unit = commit; K._process_market = pm
    def tape(p):
        def f(obs, cfg=None):
            a = acts[obs['step'] + 1][p] if obs['step'] + 1 < len(acts) else None
            return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        return f
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[tape(0), tape(1)])
    finally:
        K._commit_unit = oc; K._process_market = opm
    return dict(id=d['id'], names=d['info']['TeamNames'], rewards=d['rewards'],
                ok=[round(x) for x in r['r']] == [round(x) for x in d['rewards']],
                sales=[{f"{k[0]}:{k[1]}": v for k, v in s.items()} for s in sales],
                buys=[{f"{k[0]}:{k[1]}": v for k, v in b.items()} for b in buys])

if __name__ == '__main__':
    path, out = sys.argv[1], sys.argv[2]
    team = sys.argv[3] if len(sys.argv) > 3 else 'offhand'
    games = [g for g in json.load(open(path)) if team in g['info']['TeamNames']]
    with ProcessPoolExecutor(4) as ex, open(out, 'w') as fh:
        rows = list(ex.map(one, games))
        for r in rows: fh.write(json.dumps(r) + '\n')
    def sim(a, b, n=144):
        return sum(1 for i in range(n) if a[i].get('farmer') == b[i].get('farmer') and a[i].get('hands') == b[i].get('hands')) / n
    gmap = {g['id']: g for g in games}
    kinds = {}
    for r in rows:
        g = gmap[r['id']]; s = r['names'].index(team)
        sm = sim([a[s] for a in g['acts']], [a[1 - s] for a in g['acts']])
        kinds[r['id']] = 'copy' if sm >= 0.8 else ('near' if sm >= 0.4 else 'divergent')
    for kind in ('divergent', 'copy'):
        rs = [r for r in rows if kinds[r['id']] == kind]; n = len(rs)
        print(f"\n=== {kind}: {n} games (rec ok {sum(r['ok'] for r in rs)}) — per-week revenue delta us-them and their avg price ===")
        for prod in ('TOMATO', 'WHEAT', 'EGG', 'STRAWBERRY', 'CARROT', 'WOOL', 'MILK', 'MELON', 'FERTILIZER'):
            line = f"  {prod[:6]:6s}"
            for w0 in range(0, 30, 6):
                du = dt = uu = ut = 0.0
                for r in rs:
                    s = r['names'].index(team); o = 1 - s
                    for day in range(w0, w0 + 6):
                        a = r['sales'][s].get(f"{day}:{prod}", [0, 0]); b = r['sales'][o].get(f"{day}:{prod}", [0, 0])
                        du += a[1]; uu += a[0]; dt += b[1]; ut += b[0]
                line += f" | d{w0:02d}-{w0+5:02d}: {(du-dt)/n:+6.0f} ({(uu-ut)/n:+4.0f}u) them@{(dt/ut if ut else 0):4.0f}"
            print(line)
        print("  wheat flow per game (us | them): bought units/$, sold units/$")
        bu = bt = ct = cu = su = st = ru = rt = 0.0
        for r in rs:
            s = r['names'].index(team); o = 1 - s
            for k, v in r['buys'][s].items():
                if k.endswith(':WHEAT'): bu += v[0]; cu += v[1]
            for k, v in r['buys'][o].items():
                if k.endswith(':WHEAT'): bt += v[0]; ct += v[1]
            for k, v in r['sales'][s].items():
                if k.endswith(':WHEAT'): su += v[0]; ru += v[1]
            for k, v in r['sales'][o].items():
                if k.endswith(':WHEAT'): st += v[0]; rt += v[1]
        print(f"    us:   bought {bu/n:5.0f}u ${cu/n:6.0f} (@{cu/bu if bu else 0:.0f})  sold {su/n:5.0f}u ${ru/n:6.0f} (@{ru/su if su else 0:.0f})")
        print(f"    them: bought {bt/n:5.0f}u ${ct/n:6.0f} (@{ct/bt if bt else 0:.0f})  sold {st/n:5.0f}u ${rt/n:6.0f} (@{rt/st if st else 0:.0f})")
