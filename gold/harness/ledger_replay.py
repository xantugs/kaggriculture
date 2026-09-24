"""Replay recorded games exactly and produce per-seat ledgers: sales per product (units, revenue), purchases,
hires, land, plus daily farm composition and action-op counts. usage: ledger_replay.py out.jsonl files..."""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena')

def one(d):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    acts = d['acts']
    FARMS = [None, None]
    sales = [collections.defaultdict(lambda: [0, 0]) for _ in range(2)]
    buys = [collections.defaultdict(lambda: [0, 0]) for _ in range(2)]
    hires = [[0, 0.0], [0, 0.0]]
    land = [[0, 0.0], [0, 0.0]]
    orig_c = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = orig_c(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL':
                sales[i][item][0] += 1; sales[i][item][1] += price
            else:
                k = op + ':' + item
                buys[i][k][0] += 1; buys[i][k][1] += price
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        i = 0 if farm is FARMS[0] else 1
        if farm['money'] != m0: hires[i][0] += 1; hires[i][1] += m0 - farm['money']
    ol = K._do_buy_land
    def bl(farm, bs):
        m0 = farm['money']; ol(farm, bs)
        i = 0 if farm is FARMS[0] else 1
        if farm['money'] != m0: land[i][0] += 1; land[i][1] += m0 - farm['money']
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    K._commit_unit = commit; K._do_hire = hire; K._do_buy_land = bl; K._process_market = pm
    comp = {}
    ops = [collections.Counter(), collections.Counter()]
    def tape(p):
        def f(obs, cfg=None):
            t = obs['step']
            a = acts[t + 1][p] if t + 1 < len(acts) else None
            if not isinstance(a, dict): a = {"farmer": ["PASS"], "hands": [], "market": []}
            for u in [a.get('farmer')] + list(a.get('hands') or []):
                if isinstance(u, list) and u: ops[p][u[0]] += 1
            if obs['hour'] == 12 and obs['day'] in (3, 6, 9, 12, 15, 18, 21, 24, 27):
                for i in (0, 1):
                    c = collections.Counter()
                    for row in obs['farms'][i]['tiles']:
                        for t_ in row:
                            if t_ is None: c['empty'] += 1
                            elif t_ == 'LOCKED': pass
                            elif t_.get('kind') == 'PLANT': c[t_['crop']] += 1
                            elif t_.get('animal'): c[t_['animal']] += 1
                            else: c[t_['kind']] += 1
                    comp.setdefault(obs['day'], [None, None])[i] = dict(c)
            return a
        return f
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[tape(0), tape(1)])
    finally:
        K._commit_unit = orig_c; K._do_hire = oh; K._do_buy_land = ol; K._process_market = opm
    ok = [round(x) for x in r['r']] == [round(x) for x in d['rewards']]
    return dict(id=d['info']['EpisodeId'], names=d['info']['TeamNames'], rewards=d['rewards'], ok=ok,
                shops=r['shops'], sales=[{k: v for k, v in s.items()} for s in sales],
                buys=[{k: v for k, v in b.items()} for b in buys], hires=hires, land=land, comp=comp,
                ops=[dict(o) for o in ops])

if __name__ == '__main__':
    out = sys.argv[1]; games = []; seen = set()
    for f in sys.argv[2:]:
        for d in json.load(open(f)):
            if d['info']['EpisodeId'] in seen: continue
            seen.add(d['info']['EpisodeId']); games.append(d)
    with ProcessPoolExecutor(4) as ex, open(out, 'w') as fh:
        for r in ex.map(one, games):
            fh.write(json.dumps(r) + '\n'); fh.flush()
    print('done', len(games))
