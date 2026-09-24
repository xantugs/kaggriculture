"""Per-item sale/purchase flows for us and the rival when a candidate plays our seat from step S (prefix replay, real town)."""
import sys, os, json, lean, ident2, pfx, collections
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments.envs.kaggriculture import kaggriculture as K
def job(t):
    f, gi, cand, S = t
    d = json.load(open(f))[gi]; names = d['info']['TeamNames']; P = names.index('Khantugs Gantulga')
    farms = {}; tot = collections.defaultdict(lambda: [0, 0.0, 0, 0.0])
    oc = K._commit_unit
    def commit(op, it, price, farm, private, market, cap=100):
        ok = oc(op, it, price, farm, private, market, cap)
        p = farms.get(id(farm))
        if ok and p is not None and op in ('SELL', 'BUY_PRODUCT'):
            r = tot[('us' if p == P else 'them', it)]
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
        A = lean.load(cand)
        ag = [ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)]; ag[P] = pfx.prefixed(A, d['acts'], P, S)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._commit_unit = oc; K.interpreter = oi
    return d['id'], names[1 - P], int(r['r'][P] - r['r'][1 - P]), {'%s|%s' % k: v for k, v in tot.items()}
if __name__ == '__main__':
    ds = json.load(open(sys.argv[1])); cand = sys.argv[2]; S = int(sys.argv[3]); out = open(sys.argv[4], 'w')
    with ProcessPoolExecutor(2) as ex:
        for gid, opp, m, tot in ex.map(job, [(f, gi, cand, S) for f, gi, _ in ds]):
            out.write(json.dumps(dict(gid=gid, opp=opp, m=m, tot=tot), ensure_ascii=False) + '\n'); out.flush()
