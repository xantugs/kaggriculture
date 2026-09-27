"""Step-level identity: play base and cand on the same pinned games, record our seat's action at every step, and report
the first step where they differ next to the first step where cand's fix fired (its _GC_REPORT counter changed).
usage: esc_ident.py corpus S base cand counter out.jsonl gid[,gid...]      (env NPROC; one-game files <corpus>.d/)"""
import sys, os, json, time
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed  # noqa: E402


def _play(d, S, cand, counter):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    spawns, shops, _ = reference(d)
    orig = install_pinned(S // 24, O, spawns, shops)
    A = lean.load(cand)
    G = A.__globals__
    acts = []; fired = [None]
    inner = _prefixed(A, d['acts'], P, S)

    def f(obs, cfg=None):
        a = inner(obs, cfg)
        acts.append(json.dumps(a, sort_keys=True))
        if fired[0] is None and G.get('_GC_REPORT', {}).get(counter):
            fired[0] = int(obs['step'])
        return a
    try:
        ag = [None, None]; ag[P] = f; ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    return acts, fired[0], r['r'][P] - r['r'][O], r['tmax'][P], G.get('_GC_REPORT', {}).get(counter, 0)


def job(t):
    path, S, base, cand, counter = t
    d = json.load(open(path, encoding='utf-8'))[0]
    t0 = time.time()
    a0, _f0, m0, tm0, _c0 = _play(d, S, base, counter)
    a1, f1, m1, tm1, c1 = _play(d, S, cand, counter)
    div = next((i for i, (x, y) in enumerate(zip(a0, a1)) if x != y), None)
    return dict(gid=d['id'], opp=d['info']['TeamNames'][1 - d['info']['TeamNames'].index('offhand')], S=S,
                first_diff_step=div, first_fire_step=f1, fired_units=c1, m_base=m0, m_cand=m1,
                tmax_base=tm0, tmax_cand=tm1, ok=(div is None and f1 is None) or (f1 is not None and (div is None or div >= f1)),
                wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    corpus, S, base, cand, counter, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
    want = [int(x) for x in sys.argv[7].split(',')]
    split = corpus + '.d'
    idx = {}
    for f in os.listdir(split):
        with open(os.path.join(split, f), encoding='utf-8') as fh:
            g = json.load(fh)[0]
        if g['id'] in want:
            idx[g['id']] = os.path.join(split, f)
        del g
    jobs = [(idx[g], S, base, cand, counter) for g in want if g in idx]
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        for r in ex.map(job, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            print(json.dumps(r, ensure_ascii=False), flush=True)
