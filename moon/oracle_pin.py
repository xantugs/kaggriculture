"""Oracle: marginal value of extra goods. Pinned from S, our shed gets +K units of ITEM at the end of each day in
[D0, D1] (room permitting). Prints mean margin change vs no gift per class. Not an agent: a measurement.
usage: oracle_pin.py cand S ITEM D0 D1 K1,K2,...   (cand under arena/cand)"""
import sys, os, json, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def job(t):
    fn, cand, S, item, D0, D1, ks = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    out = {}
    for k in ks:
        orig = pinned.install_pinned(S // 24, O, spawns, shops)
        inner = K._end_of_day
        given = [0]
        def eod(state, env, day):
            r = inner(state, env, day)
            if k and D0 <= day <= D1:
                shed = state[P].observation.private['shed']
                q = max(0, min(k, 100 - sum(shed.values())))
                shed[item] = shed.get(item, 0) + q; given[0] += q
            return r
        K._end_of_day = eod
        try:
            A = lean.load(cand)
            ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            K._end_of_day = orig
        out[k] = (r['r'][P] - r['r'][O], r['r'][P], r['r'][O], given[0])
    return d['id'], out


if __name__ == '__main__':
    cand, S, item, D0, D1 = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    ks = [0] + [int(x) for x in sys.argv[6].split(',')]
    cls = json.load(open(os.path.join(HERE, 'gameclass.json')))
    files = json.load(open(os.path.join(HERE, 'g2800_list.json')))
    path = os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    res = {}
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '15'))) as ex:
        for gid, o in ex.map(job, [(f, path, S, item, D0, D1, ks) for f in files]):
            res[gid] = o
    for name, test in (('MIRROR', lambda s: s >= 0.8), ('DIVERGENT', lambda s: s < 0.8)):
        g = [x for x in res if test(cls.get(str(x), 0))]
        print(name, len(g))
        for k in ks[1:]:
            dm = [res[x][k][0] - res[x][0][0] for x in g]; du = [res[x][k][1] - res[x][0][1] for x in g]
            dt = [res[x][k][2] - res[x][0][2] for x in g]; gv = [res[x][k][3] for x in g]
            w = sum(res[x][k][0] > 0 for x in g) - sum(res[x][0][0] > 0 for x in g)
            print(f"  +{k}/day: given {st.mean(gv):5.1f}  margin {st.mean(dm):+7.0f} ±{st.pstdev(dm) / len(g) ** .5:4.0f}  us {st.mean(du):+7.0f}  them {st.mean(dt):+7.0f}  dW {w:+d}  per unit {st.mean(dm) / max(1e-9, st.mean(gv)):+.1f}")
