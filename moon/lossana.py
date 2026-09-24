"""Loss anatomy for a file of recorded games: opponent, margin, farm similarity at days 6/15, and the per-product
net revenue difference (us - them) by period. usage: lossana.py games.json"""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from classify import sig, sim


def job(t):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    f, i = t
    d = json.load(open(os.path.join(HERE, f), encoding='utf-8'))[i]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    FARMS = [None, None]; STEP = [0]; L = collections.Counter(); snaps = {}
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            side = 1 if farm is FARMS[P] else -1
            win = 'a' if STEP[0] < 360 else ('b' if STEP[0] < 672 else 'c')
            key = item if op in ('SELL', 'BUY_PRODUCT') else op
            L[(win, key)] += side * (price if op == 'SELL' else -price)
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        L[('a' if STEP[0] < 360 else 'b', 'HIRE')] += (1 if farm is FARMS[P] else -1) * (farm['money'] - m0)
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]; STEP[0] = state[0].observation.step
        if STEP[0] in (143, 359):
            snaps[STEP[0]] = sim(sig(FARMS[P]), sig(FARMS[O]))
        return opm(state, env)
    K._commit_unit = commit; K._do_hire = hire; K._process_market = pm
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit = oc; K._do_hire = oh; K._process_market = opm
    return d['id'], names[O], d['rewards'][P] - d['rewards'][O], snaps.get(143, 0), snaps.get(359, 0), {'|'.join(k): v for k, v in L.items()}


if __name__ == '__main__':
    f = sys.argv[1]
    n = len(json.load(open(os.path.join(HERE, f), encoding='utf-8')))
    with ProcessPoolExecutor(8) as ex:
        res = list(ex.map(job, [(f, i) for i in range(n)]))
    groups = collections.defaultdict(list)
    for r in res:
        c = 'mirror15' if r[4] >= 0.8 else ('mirror6' if r[3] >= 0.9 else 'other')
        groups[c].append(r)
    for c, rs in groups.items():
        print(f"== {c}: {len(rs)} losses, mean {sum(r[2] for r in rs)/len(rs):+.0f}, close(<3k) {sum(1 for r in rs if r[2] > -3000)}")
        tot = collections.Counter()
        for r in rs:
            for k, v in r[5].items(): tot[k] += v
        print('   ', '  '.join(f"{k} {v/len(rs):+.0f}" for k, v in sorted(tot.items(), key=lambda kv: kv[1])[:10]))
        print('   ', '  '.join(f"{k} {v/len(rs):+.0f}" for k, v in sorted(tot.items(), key=lambda kv: -kv[1])[:5]))
        for r in sorted(rs, key=lambda r: r[2])[:12]:
            print(f"    {r[1][:22]:22s} {r[2]:+8.0f}  sim6 {r[3]:.2f} sim15 {r[4]:.2f}")
