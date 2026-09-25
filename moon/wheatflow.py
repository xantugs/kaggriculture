"""Where does extra wheat go? Oracle fertilizing (K per day, wheat/carrot) vs none on N games: wheat harvested,
sold (units, $), bought, fed, discarded at end of day (shed overflow), left at the end. usage: wheatflow.py cand K N"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def job(t):
    fn, cand, k = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(4, O, spawns, shops)
    inner = K._end_of_day
    c = collections.Counter(); FARM = [None]; PRIV = [None]
    def eod(state, env, day):
        priv = state[P].observation.private
        before = sum(priv['shed'].values()) + sum(sum(v.values()) for v in priv['inventories'])
        wb = priv['shed'].get('WHEAT', 0) + sum(v.get('WHEAT', 0) for v in priv['inventories'])
        r = inner(state, env, day)
        wa = priv['shed'].get('WHEAT', 0)
        c['wheat_discarded'] += wb - wa
        c['all_discarded'] += before - sum(priv['shed'].values())
        if k and 5 <= day <= 28:
            farm = state[0].observation.farms[P]; n = 0
            for row in farm['tiles']:
                for t in row:
                    if isinstance(t, dict) and t.get('kind') == 'PLANT' and t['crop'] in ('WHEAT', 'CARROT') and day + 1 - t['planted_day'] == 2 and t.get('fertilized_until_day', -1) < day + 3 and n < k:
                        t['fertilized_until_day'] = day + 3; n += 1
                        if priv['shed'].get('FERTILIZER', 0) > 0:
                            priv['shed']['FERTILIZER'] -= 1
        return r
    oau, ocu, opm = K._apply_unit_action, K._commit_unit, K._process_market
    def au(farm, private, idx, action, bs, day, tpd, cap=100):
        if farm is FARM[0] and isinstance(action, list) and action:
            inv = K._farmer_inventory(private, idx); w0 = inv.get('WHEAT', 0); s0 = private['shed'].get('WHEAT', 0)
            r = oau(farm, private, idx, action, bs, day, tpd, cap)
            w1 = inv.get('WHEAT', 0); s1 = private['shed'].get('WHEAT', 0)
            if action[0] == 'HARVEST' and w1 > w0: c['harvested'] += w1 - w0
            if action[0] == 'FEED' and w1 < w0: c['fed'] += w0 - w1
            return r
        return oau(farm, private, idx, action, bs, day, tpd, cap)
    def cu(op, item, price, farm, private, market, cap=100):
        ok = ocu(op, item, price, farm, private, market, cap)
        if ok and farm is FARM[0] and item == 'WHEAT':
            c[op + '_n'] += 1; c[op + '_$'] += price
        return ok
    def pm(state, env):
        FARM[0] = state[0].observation.farms[P]; PRIV[0] = state[P].observation.private
        return opm(state, env)
    K._end_of_day = eod; K._apply_unit_action, K._commit_unit, K._process_market = au, cu, pm
    try:
        A = lean.load(cand)
        ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._apply_unit_action, K._commit_unit, K._process_market = oau, ocu, opm
    c['left_end'] = PRIV[0]['shed'].get('WHEAT', 0)
    c['margin'] = r['r'][P] - r['r'][O]; c['us'] = r['r'][P]
    return k, c


if __name__ == '__main__':
    cand, k, N = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    files = json.load(open(os.path.join(HERE, 'g2800_list.json')))[:N]
    path = os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    tot = {0: collections.Counter(), k: collections.Counter()}
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '15'))) as ex:
        for kk, c in ex.map(job, [(f, path, kk) for f in files for kk in (0, k)]):
            tot[kk].update(c)
    for key in sorted(set(tot[0]) | set(tot[k])):
        print(f'  {key:16s} {tot[0][key] / N:9.1f} -> {tot[k][key] / N:9.1f}  ({(tot[k][key] - tot[0][key]) / N:+.1f})')
