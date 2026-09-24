"""Per-product net revenue (sales - buys) and hires, us vs them, by day window, in recorded games of a class.
usage: closeloss.py class maxloss   (e.g. mirror15 3000 -> losses with margin in (-3000, 0))"""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import pinmulti


def job(t):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    f, i = t
    d = json.load(open(os.path.join(HERE, f), encoding='utf-8'))[i]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    FARMS = [None, None]; STEP = [0]
    L = collections.Counter()
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            side = 'us' if farm is FARMS[P] else 'them'
            win = 'd0-14' if STEP[0] < 360 else ('d15-27' if STEP[0] < 672 else 'd28-29')
            sign = 1 if op == 'SELL' else -1
            L[(side, win, item if op in ('SELL', 'BUY_PRODUCT') else op)] += sign * price
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        L[('us' if farm is FARMS[P] else 'them', 'd0-14' if STEP[0] < 360 else 'd15-29', 'HIRE')] += farm['money'] - m0
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]; STEP[0] = state[0].observation.step
        return opm(state, env)
    K._commit_unit = commit; K._do_hire = hire; K._process_market = pm
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit = oc; K._do_hire = oh; K._process_market = opm
    return d['id'], names[O], d['rewards'][P] - d['rewards'][O], dict((('|'.join(k)), v) for k, v in L.items())


if __name__ == '__main__':
    want, mx = sys.argv[1], float(sys.argv[2])
    cls = {r['gid']: r for r in json.load(open(os.path.join(HERE, 'opp_class.json'), encoding='utf-8'))}
    def c(r): return 'mirror15' if r['sim359'] >= 0.8 else ('mirror6' if r['sim143'] >= 0.9 else 'other')
    games = []
    for f, i in pinmulti.load_games():
        gid = json.load(open(os.path.join(HERE, f), encoding='utf-8'))[i]['id']
        r = cls.get(gid)
        if r and c(r) == want and -mx < r['rec'] < 0:
            games.append((f, i))
    with ProcessPoolExecutor(4) as ex:
        res = list(ex.map(job, games))
    tot = collections.Counter()
    for gid, opp, m, L in res:
        for k, v in L.items():
            side, win, item = k.split('|')
            tot[(win, item)] += v if side == 'us' else -v
    n = len(res)
    print(n, 'games; mean margin', round(sum(r[2] for r in res) / n))
    for (win, item), v in sorted(tot.items(), key=lambda kv: kv[1]):
        if abs(v / n) >= 50:
            print(f"  {win:7s} {item:14s} {v/n:+8.0f}")
