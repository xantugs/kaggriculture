
# ---- moon parameter search (hill climb from the current best, closed loop vs v15b, decoupled engine) ----
import os, sys, json, time, random
sys.path.insert(0, '/kaggle/working')
from concurrent.futures import ProcessPoolExecutor

W = '/kaggle/working'
BASE_SRC = open(os.path.join(W, 'base.py'), encoding='utf-8').read()
MOON_SRC = open(os.path.join(W, 'moon.py'), encoding='utf-8').read()


def build(cfg, tag):
    cfg = dict(cfg); start = cfg.pop('start', 360)
    layer = MOON_SRC.replace('_MOON = Moon()', 'MOON_P.update(%r)\nMOON_START = %r\n_MOON = Moon()' % (cfg, start), 1)
    path = os.path.join(W, 'cand_%s.py' % tag)
    open(path, 'w', encoding='utf-8').write(BASE_SRC.rstrip() + '\n\n' + layer)
    return path


def game(t):
    path, seed, seat = t
    try:
        import lean, decouple
        decouple.install(0)
        A = lean.load(path); B = lean.load(os.path.join(W, 'base.py'))
        r = lean.play(None, None, seed, agent_objs=[A, B] if seat == 0 else [B, A])
        us, them = r['r'][seat], r['r'][1 - seat]
        return (path, seed, seat, us - them)
    except Exception as e:
        return (path, seed, seat, None)


def evaluate(ex, cfgs, seeds):
    paths = [build(c, 'r%d_%d' % (ROUND[0], i)) for i, c in enumerate(cfgs)]
    jobs = [(p, s, st) for p in paths for s in seeds for st in (0, 1)]
    res = {p: [] for p in paths}
    for p, s, st, m in ex.map(game, jobs, chunksize=1):
        if m is not None:
            res[p].append(m)
    out = []
    for c, p in zip(cfgs, paths):
        ms = res[p]; n = max(1, len(ms))
        mean = sum(ms) / n; wins = sum(m > 0 for m in ms)
        sd = (sum((m - mean) ** 2 for m in ms) / n) ** 0.5
        out.append(dict(cfg=c, mean=mean, wins=wins, n=len(ms), se=sd / n ** 0.5))
    return out


def mutate(cfg, rng, k):
    c = dict(cfg)
    for key in rng.sample(sorted(SPACE), k):
        c[key] = rng.choice(SPACE[key])
    return c


ROUND = [0]
if __name__ == '__main__':
    t0 = time.time()
    rng = random.Random(SEED0)
    workers = max(4, (os.cpu_count() or 4) - 2)
    print('cpus', os.cpu_count(), 'workers', workers, flush=True)
    seeds = list(range(0, N_SEEDS))
    confirm = list(range(5000, 5000 + N_SEEDS))
    log = open(os.path.join(W, 'search_log.jsonl'), 'a')
    with ProcessPoolExecutor(workers) as ex:
        best = evaluate(ex, [BEST0], seeds)[0]
        print('BASE', json.dumps({k: best[k] for k in ('mean', 'wins', 'n', 'se')}), flush=True)
        log.write(json.dumps(dict(round=0, **best)) + '\n'); log.flush()
        while time.time() - t0 < BUDGET:
            ROUND[0] += 1
            cands = [mutate(best['cfg'], rng, rng.choice((1, 1, 2, 3, 4))) for _ in range(PER_ROUND)]
            rs = evaluate(ex, cands, seeds)
            for r in rs:
                log.write(json.dumps(dict(round=ROUND[0], **r)) + '\n')
            log.flush()
            top = max(rs, key=lambda r: r['mean'])
            msg = 'round %d best-so-far %.0f | round top %.0f (%d/%d) %s' % (ROUND[0], best['mean'], top['mean'], top['wins'], top['n'],
                                                                         {k: v for k, v in top['cfg'].items() if best['cfg'].get(k) != v})
            if top['mean'] > best['mean'] + 150:
                # confirm on fresh seeds against the incumbent before accepting
                chk = evaluate(ex, [top['cfg'], best['cfg']], confirm)
                if chk[0]['mean'] > chk[1]['mean']:
                    best = dict(top); msg += ' ACCEPT (confirm %.0f vs %.0f)' % (chk[0]['mean'], chk[1]['mean'])
                else:
                    msg += ' reject (confirm %.0f vs %.0f)' % (chk[0]['mean'], chk[1]['mean'])
            print(msg, round(time.time() - t0), 's', flush=True)
            json.dump(best, open(os.path.join(W, 'best.json'), 'w'))
    print('FINAL', json.dumps(best), flush=True)
