"""Oracle: value of extra fertilizing labor. Pinned from S; at the end of each day d in [D0, D1] up to K of our tiles
get fertilizer as if an extra hand had fertilized them on day d+1 before the tape watered them:
  strawberry with production tomorrow at age 9 or 13 -> covers that event and the next (2 events)
  wheat / carrot reaching age 2 tomorrow -> covers the whole watering window (MODE best: ages 2-4) or, MODE safe,
  only as if fertilized at age 1 (ages 1-3)
Each application takes one FERTILIZER from the shed (or $FC if none); each day with >= 1 application costs $H.
usage: oracle_fert.py cand S D0 D1 CROPS K1,K2,.. H FC MODE"""
import sys, os, json, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def job(t):
    fn, cand, S, D0, D1, crops, ks, H, FC, mode = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    out = {}
    for k in ks:
        orig = pinned.install_pinned(S // 24, O, spawns, shops)
        inner = K._end_of_day
        used = [0, 0]
        def eod(state, env, day):
            r = inner(state, env, day)
            if not k or not D0 <= day <= D1:
                return r
            farm = state[0].observation.farms[P]; priv = state[P].observation.private
            cand_t = []
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if not (isinstance(t, dict) and t.get('kind') == 'PLANT') or t['crop'] not in crops:
                        continue
                    age1 = day + 1 - t['planted_day']; fu = t.get('fertilized_until_day', -1)
                    if t['crop'] == 'STRAWBERRY' and age1 in (9, 13) and fu < day + 3:
                        cand_t.append((0, t, day + 3))
                    elif t['crop'] in ('WHEAT', 'CARROT') and age1 == 2:
                        tgt = day + 3 if mode == 'best' else day + 2
                        if fu < tgt:
                            cand_t.append((1 if t['crop'] == 'WHEAT' else 2, t, tgt))
            cand_t.sort(key=lambda c: c[0])
            n = 0
            for _, t, tgt in cand_t[:k]:
                t['fertilized_until_day'] = tgt; n += 1
                if priv['shed'].get('FERTILIZER', 0) > 0:
                    priv['shed']['FERTILIZER'] -= 1
                else:
                    farm['money'] -= FC
            if n:
                farm['money'] -= H
            used[0] += n; used[1] += 1 if n else 0
            return r
        K._end_of_day = eod
        try:
            A = lean.load(cand)
            ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            K._end_of_day = orig
        out[k] = (r['r'][P] - r['r'][O], r['r'][P], r['r'][O], used[0], used[1])
    return os.path.basename(fn)[:-5], out


if __name__ == '__main__':
    cand, S, D0, D1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    crops = set(sys.argv[5].split(',')); ks = [0] + [int(x) for x in sys.argv[6].split(',')]
    H, FC, mode = float(sys.argv[7]), float(sys.argv[8]), sys.argv[9]
    cls = json.load(open(os.path.join(HERE, os.environ.get('GCLASS', 'gameclass.json'))))
    files = json.load(open(os.path.join(HERE, os.environ.get('GLIST', 'g2800_list.json'))))
    if len(sys.argv) > 10:
        files = files[:int(sys.argv[10])]
    path = os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    res = {}
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '15'))) as ex:
        for gid, o in ex.map(job, [(f, path, S, D0, D1, crops, ks, H, FC, mode) for f in files]):
            res[gid] = o
    for name, test in (('MIRROR', lambda s: s >= 0.8), ('DIVERGENT', lambda s: s < 0.8)):
        g = [x for x in res if test(cls.get(str(x), 0))]
        if not g:
            continue
        print(name, len(g), 'base wins', sum(res[x][0][0] > 0 for x in g))
        for k in ks[1:]:
            dm = [res[x][k][0] - res[x][0][0] for x in g]; du = [res[x][k][1] - res[x][0][1] for x in g]
            dt = [res[x][k][2] - res[x][0][2] for x in g]
            w = sum(res[x][k][0] > 0 for x in g) - sum(res[x][0][0] > 0 for x in g)
            print(f"  K={k:2d}: ferts {st.mean(res[x][k][3] for x in g):5.1f} days {st.mean(res[x][k][4] for x in g):4.1f}  margin {st.mean(dm):+7.0f} ±{st.pstdev(dm) / len(g) ** .5:4.0f}  us {st.mean(du):+7.0f}  them {st.mean(dt):+7.0f}  dW {w:+d}")
