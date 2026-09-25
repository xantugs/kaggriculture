"""Candidate played pinned from step S on the per-game files; records every sale (both sides) with the seller's shed
at that moment. Prints per-item units/avg price for us and them (days D0-D1) by class, and a sample of our cheapest
sales. usage: saleprof_pin.py cand S [D0 D1] [MIRROR|DIVERGENT|ALL]   (writes saleprof_<cand>.json)"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def job(t):
    fn, cand, S = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(S // 24, O, spawns, shops)
    F = [None, None]; ST = [0]; sales = []
    oc, opm = K._commit_unit, K._process_market
    def commit(op, it, price, farm, private, market, cap=100):
        held = private['shed'].get(it, 0); tot = sum(private['shed'].values())
        ok = oc(op, it, price, farm, private, market, cap)
        if ok and op == 'SELL' and ST[0] >= S:
            sales.append((ST[0], it, price, 0 if farm is F[P] else 1, held, tot))
        return ok
    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]; ST[0] = state[0].observation.step
        return opm(state, env)
    K._commit_unit, K._process_market = commit, pm
    try:
        A = lean.load(cand)
        ag = [None, None]
        ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit, K._process_market = oc, opm
    return d['id'], sales, (r['r'][P] - r['r'][O]) if r['r'][P] is not None else None


if __name__ == '__main__':
    cand, S = sys.argv[1], int(sys.argv[2])
    D0, D1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 29)
    klass = sys.argv[5] if len(sys.argv) > 5 else 'MIRROR'
    cls = json.load(open(os.path.join(HERE, 'gameclass.json')))
    files = [f for f in json.load(open(os.path.join(HERE, 'g2800_list.json')))
             if klass == 'ALL' or (cls.get(os.path.basename(f)[:-5], 0) >= 0.8) == (klass == 'MIRROR')]
    path = cand if os.path.exists(cand) else os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    out = {}
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '14'))) as ex:
        for gid, sales, m in ex.map(job, [(f, path, S) for f in files]):
            out[gid] = dict(sales=sales, m=m)
    json.dump(out, open(os.path.join(HERE, 'saleprof_%s_%s.json' % (os.path.basename(path)[:-3], klass)), 'w'))
    g = len(out)
    agg = collections.defaultdict(lambda: [[0, 0], [0, 0]])
    cheap = []
    for gid, o in out.items():
        for s, it, p, who, held, tot in o['sales']:
            if D0 * 24 <= s < (D1 + 1) * 24:
                agg[it][who][0] += 1; agg[it][who][1] += p
                if who == 0 and it == 'STRAWBERRY' and p < 60:
                    cheap.append((gid, s // 24, s % 24, p, held, tot))
    print(f"{cand} {klass} games {g}, mean margin {sum(o['m'] for o in out.values()) / g:+.0f}, wins {sum(o['m'] > 0 for o in out.values())}")
    for it, ((un, ur), (tn, tr)) in sorted(agg.items(), key=lambda kv: -(kv[1][0][1] + kv[1][1][1])):
        print(f"  {it:10s} us {un / g:6.1f} @ {ur / max(1, un):6.1f} = {ur / g:7.0f}   them {tn / g:6.1f} @ {tr / max(1, tn):6.1f} = {tr / g:7.0f}   gap {(tr - ur) / g:+6.0f}")
    print('cheap strawberry sales (gid day hour price held shedtotal):', len(cheap))
    for c in cheap[:40]:
        print('  ', c)
