"""Our recorded games vs chassis copies: farm similarity at steps 143/359, then per-product revenue/cost of them minus
us from step S to the end, and the step where their actions first diverge from ours in a way that changes the farm.
usage: mirrordiff.py games.json [S] [min_sim]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def sig(t):
    if t is None or t == 'LOCKED': return str(t)
    if t.get('kind') == 'WEED': return None
    return (t.get('kind'), t.get('crop'), t.get('animal'))


def sim(fa, fb):
    same = n = 0
    for y in range(10):
        for x in range(10):
            a, b = sig(fa['tiles'][y][x]), sig(fb['tiles'][y][x])
            if a is None or b is None: continue
            n += 1; same += a == b
    return same / max(1, n)


def job(t):
    d, S = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    n = d['info']['TeamNames']; P = n.index('offhand'); O = 1 - P
    led = [collections.Counter(), collections.Counter()]; F = [None, None]; ST = [0]; sims = {}
    oc, oh, opm = K._commit_unit, K._do_hire, K._process_market
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and ST[0] >= S:
            k = 0 if farm is F[P] else 1
            if op == 'SELL': led[k][item] += price; led[k]['n_' + item] += 1
            else: led[k][op + ':' + item] -= price
        return ok
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if ST[0] >= S: led[0 if farm is F[P] else 1]['HIRE'] += farm['money'] - m0
    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]; ST[0] = state[0].observation.step
        if ST[0] in (143, 359, 503, 647): sims[ST[0]] = sim(F[P], F[O])
        return opm(state, env)
    K._commit_unit, K._do_hire, K._process_market = commit, hire, pm
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._commit_unit, K._do_hire, K._process_market = oc, oh, opm
    if [int(x) for x in r['r']] != [int(x) for x in d['rewards']]:
        return None
    return dict(gid=d['id'], opp=n[O], m=d['rewards'][P] - d['rewards'][O], sims=sims, us=dict(led[0]), them=dict(led[1]))


if __name__ == '__main__':
    f = sys.argv[1]; S = int(sys.argv[2]) if len(sys.argv) > 2 else 360; ms = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
    games = json.load(open(f, encoding='utf-8'))
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '8'))) as ex:
        res = [r for r in ex.map(job, [(d, S) for d in games]) if r]
    json.dump({str(r['gid']): r['sims'].get(359, 0) for r in res}, open(os.path.join(HERE, 'gameclass.json'), 'w'))
    mir = [r for r in res if r['sims'].get(359, 0) >= ms]
    div = [r for r in res if r['sims'].get(359, 0) < ms]
    for name, grp in (('MIRRORS (sim359 >= %.2f)' % ms, mir), ('DIVERGENT', div)):
        if not grp: continue
        w = sum(r['m'] > 0 for r in grp)
        print(f"{name}: games {len(grp)}  our wins {w}  mean margin {sum(r['m'] for r in grp) / len(grp):+.0f}  "
              f"sim143 {sum(r['sims'].get(143, 0) for r in grp) / len(grp):.2f} sim359 {sum(r['sims'].get(359, 0) for r in grp) / len(grp):.2f} "
              f"sim503 {sum(r['sims'].get(503, 0) for r in grp) / len(grp):.2f} sim647 {sum(r['sims'].get(647, 0) for r in grp) / len(grp):.2f}")
        keys = sorted({k for r in grp for k in list(r['us']) + list(r['them']) if not k.startswith('n_')})
        diffs = []
        for k in keys:
            dv = sum(r['them'].get(k, 0) - r['us'].get(k, 0) for r in grp) / len(grp)
            nu = sum(r['us'].get('n_' + k, 0) for r in grp) / len(grp); nt = sum(r['them'].get('n_' + k, 0) for r in grp) / len(grp)
            diffs.append((dv, k, nu, nt))
        for dv, k, nu, nt in sorted(diffs, key=lambda x: -abs(x[0]))[:12]:
            extra = f"  units us {nu:6.1f} them {nt:6.1f}" if nu or nt else ''
            print(f"   {k:24s} them-us {dv:+8.0f}{extra}")
        opps = collections.Counter(r['opp'] for r in grp)
        print('   opponents:', dict(opps.most_common(10)))
