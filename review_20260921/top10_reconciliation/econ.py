"""Economic breakdown of a recorded episode (both seats replayed from their recorded actions):
per-player sales by item (units, revenue, avg price), purchases (seeds, animals, land, hires), and
per-day farm composition snapshots."""
import sys, json, collections, lean, ident2
from kaggle_environments.envs.kaggriculture import kaggriculture as K

def analyze(d):
    cur = {'step': 0}; farms = {}
    sales = [collections.defaultdict(lambda: [0, 0]) for _ in range(2)]
    buys = [collections.defaultdict(lambda: [0, 0]) for _ in range(2)]
    hires = [[0, 0], [0, 0]]; land = [[0, 0], [0, 0]]
    comp = {}
    oc = K._commit_unit
    def commit(op, it, price, farm, private, market, cap=100):
        ok = oc(op, it, price, farm, private, market, cap)
        p = farms.get(id(farm), -1)
        if ok and p >= 0:
            if op == 'SELL':
                sales[p][it][0] += 1; sales[p][it][1] += price
            else:
                buys[p][op + ':' + it][0] += 1; buys[p][op + ':' + it][1] += price
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult):
        m0 = farm['money']; oh(farm, private, bs, mult)
        p = farms.get(id(farm), -1)
        if p >= 0 and farm['money'] < m0: hires[p][0] += 1; hires[p][1] += m0 - farm['money']
    ol = K._do_buy_land
    def bl(farm, bs):
        m0 = farm['money']; ol(farm, bs)
        p = farms.get(id(farm), -1)
        if p >= 0 and farm['money'] < m0: land[p][0] += 1; land[p][1] += m0 - farm['money']
    oi = K.interpreter
    def interp(state, env):
        o = state[0].observation
        if hasattr(o, 'farms') and o.farms:
            farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1
            cur['step'] = o.get('step', 0)
            s = cur['step']
            if s % 24 == 23:
                snap = []
                for f in o.farms:
                    c = collections.Counter()
                    for row in f['tiles']:
                        for t in row:
                            if isinstance(t, dict):
                                c[t.get('animal') or t.get('crop') or t.get('kind')] += 1
                            elif t is None: c['empty'] += 1
                    snap.append((dict(c), f['money'], len(f.get('hands') or [])))
                comp[s // 24] = snap
        return oi(state, env)
    K._commit_unit = commit; K._do_hire = hire; K._do_buy_land = bl; K.interpreter = interp
    try:
        acts = d['acts']
        r = lean.play(None, None, d['info']['seed'], agent_objs=[ident2._tape(acts, 0), ident2._tape(acts, 1)])
    finally:
        K._commit_unit = oc; K._do_hire = oh; K._do_buy_land = ol; K.interpreter = oi
    ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
    def dd(x): return {k: list(v) for k, v in x.items()}
    return {'id': d['id'], 'names': d['info']['TeamNames'], 'rewards': d['rewards'], 'ok': ok,
            'sales': [dd(s) for s in sales], 'buys': [dd(b) for b in buys], 'hires': hires, 'land': land, 'comp': comp}

if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor
    import glob
    files = sorted(glob.glob(sys.argv[1]))
    def job(f):
        return analyze(json.load(open(f))[0])
    with ProcessPoolExecutor(2) as ex:
        for res in ex.map(job, files):
            print(json.dumps(res), flush=True)
