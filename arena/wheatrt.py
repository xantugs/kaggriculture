"""Per game: wheat trading totals (units, net $) for us and the rival; count of same-step buy+sell round trips."""
import sys, json, glob, collections, lean, ident2
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments.envs.kaggriculture import kaggriculture as K
def job(t):
    f, i = t
    d = json.load(open(f))[i]; names = d['info']['TeamNames']; P = names.index('Khantugs Gantulga')
    farms = {}; cur = {'s': 0}; tot = [[0, 0.0, 0, 0.0], [0, 0.0, 0, 0.0]]
    oc = K._commit_unit
    def commit(op, it, price, farm, private, market, cap=100):
        ok = oc(op, it, price, farm, private, market, cap)
        p = farms.get(id(farm))
        if ok and it == 'WHEAT' and p is not None and op in ('SELL', 'BUY_PRODUCT'):
            k = 0 if p == P else 1
            if op == 'SELL': tot[k][0] += 1; tot[k][1] += price
            else: tot[k][2] += 1; tot[k][3] += price
        return ok
    oi = K.interpreter
    def interp(state, env):
        o = state[0].observation
        if hasattr(o, 'farms') and o.farms: farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1; cur['s'] = o.get('step', 0)
        return oi(state, env)
    K._commit_unit = commit; K.interpreter = interp
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)])
    finally:
        K._commit_unit = oc; K.interpreter = oi
    # same-step round trips in the recorded orders
    rt = [0, 0]
    for s in range(1, len(d['acts'])):
        for k, pl in ((0, P), (1, 1 - P)):
            a = d['acts'][s][pl]
            if not isinstance(a, dict): continue
            ops = [(o[0], o[1]) for o in (a.get('market') or []) if o and len(o) > 1]
            if ('BUY_PRODUCT', 'WHEAT') in ops and ('SELL', 'WHEAT') in ops: rt[k] += 1
    m = d['rewards'][P] - d['rewards'][1 - P]
    return d['id'], names[1 - P][:14], m, [round(tot[0][1] - tot[0][3]), tot[0][0], tot[0][2]], [round(tot[1][1] - tot[1][3]), tot[1][0], tot[1][2]], rt
if __name__ == '__main__':
    G = [(f, i) for f in sorted(glob.glob(sys.argv[1])) for i in range(len(json.load(open(f))))]
    with ProcessPoolExecutor(2) as ex:
        for gid, opp, m, us, them, rt in ex.map(job, G):
            print(gid, '%-14s' % opp, 'margin %6d' % m, '| wheat net us %6d (sold %4d bought %4d) them %6d (sold %4d bought %4d) | diff %6d | same-step RT us %d them %d' % (us[0], us[1], us[2], them[0], them[1], them[2], us[0] - them[0], rt[0], rt[1]), flush=True)
