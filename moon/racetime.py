"""Sale timing of one product in our recorded games vs a class of opponents: per hour, units and mean price for us and
them (days D0-D1), and per day who sold first / first-sale price. usage: racetime.py ITEM D0 D1 [MIRROR|DIVERGENT]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def job(t):
    fn, item, D0, D1 = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    n = d['info']['TeamNames']; P = n.index('offhand')
    F = [None, None]; S = [0]; sales = []
    oc, opm = K._commit_unit, K._process_market
    def commit(op, it, price, farm, private, market, cap=100):
        ok = oc(op, it, price, farm, private, market, cap)
        if ok and op == 'SELL' and it == item and D0 * 24 <= S[0] < (D1 + 1) * 24:
            sales.append((S[0], 0 if farm is F[P] else 1, price))
        return ok
    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]; S[0] = state[0].observation.step
        return opm(state, env)
    K._commit_unit, K._process_market = commit, pm
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._process_market = oc, opm
    return d['id'], sales


if __name__ == '__main__':
    item, D0, D1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); klass = sys.argv[4] if len(sys.argv) > 4 else 'MIRROR'
    cls = json.load(open(os.path.join(HERE, 'gameclass.json')))
    files = [f for f in json.load(open(os.path.join(HERE, 'g2800_list.json')))
             if (cls.get(os.path.basename(f)[:-5], 0) >= 0.8) == (klass == 'MIRROR')]
    hr = [collections.Counter(), collections.Counter()]; hp = [collections.Counter(), collections.Counter()]
    first = collections.Counter(); fp = [[], []]; tot = [[0, 0], [0, 0]]
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '8'))) as ex:
        for gid, sales in ex.map(job, [(f, item, D0, D1) for f in files]):
            byday = collections.defaultdict(lambda: [None, None])
            for s, who, p in sales:
                h = s % 24; hr[who][h] += 1; hp[who][h] += p; tot[who][0] += 1; tot[who][1] += p
                if byday[s // 24][who] is None: byday[s // 24][who] = (s, p)
            for day, (a, b) in byday.items():
                if a and b:
                    first['us' if a[0] < b[0] else ('them' if b[0] < a[0] else 'same')] += 1
                    fp[0].append(a[1]); fp[1].append(b[1])
    g = len(files)
    print(f"{item} days {D0}-{D1}, {klass} games {g}: us {tot[0][0] / g:.1f} units @ {tot[0][1] / max(1, tot[0][0]):.1f}   them {tot[1][0] / g:.1f} @ {tot[1][1] / max(1, tot[1][0]):.1f}")
    print('  first seller per day:', dict(first), f" first-sale price us {sum(fp[0]) / max(1, len(fp[0])):.1f} them {sum(fp[1]) / max(1, len(fp[1])):.1f}")
    for h in range(24):
        if hr[0][h] or hr[1][h]:
            print(f"  h{h:02d}  us {hr[0][h] / g:5.2f} @ {hp[0][h] / max(1, hr[0][h]):6.1f}   them {hr[1][h] / g:5.2f} @ {hp[1][h] / max(1, hr[1][h]):6.1f}")
