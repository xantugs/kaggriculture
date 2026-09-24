"""Per game and product: units and $ of sales/purchases for us and the rival (hooked _commit_unit)."""
import sys, json, glob, lean, ident2, collections
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments.envs.kaggriculture import kaggriculture as K
def job(t):
    f, i = t
    d = json.load(open(f))[i]; names = d['info']['TeamNames']; P = names.index('Khantugs Gantulga')
    farms = {}; tot = collections.defaultdict(lambda: [0, 0.0, 0, 0.0])
    oc = K._commit_unit
    def commit(op, it, price, farm, private, market, cap=100):
        ok = oc(op, it, price, farm, private, market, cap)
        p = farms.get(id(farm))
        if ok and p is not None and op in ('SELL', 'BUY_PRODUCT'):
            k = 'us' if p == P else 'them'
            r = tot[(k, it)]
            if op == 'SELL': r[0] += 1; r[1] += price
            else: r[2] += 1; r[3] += price
        return ok
    oi = K.interpreter
    def interp(state, env):
        o = state[0].observation
        if hasattr(o, 'farms') and o.farms: farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1
        return oi(state, env)
    K._commit_unit = commit; K.interpreter = interp
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)])
    finally:
        K._commit_unit = oc; K.interpreter = oi
    m = d['rewards'][P] - d['rewards'][1 - P]
    return d['id'], names[1 - P], m, {'%s|%s' % k: v for k, v in tot.items()}
if __name__ == '__main__':
    G = [(f, i) for f in sorted(glob.glob(sys.argv[1])) for i in range(len(json.load(open(f))))]
    out = open(sys.argv[2], 'w')
    with ProcessPoolExecutor(1) as ex:
        for gid, opp, m, tot in ex.map(job, G):
            out.write(json.dumps(dict(gid=gid, opp=opp, m=m, tot=tot), ensure_ascii=False) + '\n'); out.flush()
