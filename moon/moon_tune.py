"""Random search over MOON_P knobs against an opponent, paired seeds, both seats.
usage: tune.py space.json opp seeds n_configs out.jsonl [start]
Each config is built from the current moon.py; results are appended with the config."""
import sys, os, json, random, time, subprocess
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import batch


def build(cfg, path):
    base = open(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v12.py'), encoding='utf-8').read()
    layer = open(os.path.join(HERE, 'moon.py'), encoding='utf-8').read()
    ov = {k: v for k, v in cfg.items() if k != 'start'}
    layer = layer.replace('_MOON = Moon()', 'MOON_P.update(%r)\nMOON_START = %r\n_MOON = Moon()' % (ov, cfg.get('start', 144)), 1)
    open(path, 'w', encoding='utf-8').write(base.rstrip() + '\n\n\n' + layer)


if __name__ == '__main__':
    space = json.load(open(sys.argv[1]))
    opp = sys.argv[2]; seeds = batch.seeds_of(sys.argv[3]); n = int(sys.argv[4]); out = sys.argv[5]
    start = int(sys.argv[6]) if len(sys.argv) > 6 else 360
    os.makedirs(os.path.join(HERE, 'tune_c'), exist_ok=True)
    rng = random.Random(int(time.time()))
    cfgs = [{'start': start}]
    for _ in range(n - 1):
        c = {'start': start}
        for k, vals in space.items():
            if rng.random() < 0.5:
                c[k] = rng.choice(vals)
        cfgs.append(c)
    with ProcessPoolExecutor(16) as ex:
        for ci, cfg in enumerate(cfgs):
            path = os.path.join(HERE, 'tune_c', 'c%d_%d.py' % (os.getpid(), ci))
            build(cfg, path)
            jobs = [(path, opp, s, st) for s in seeds for st in (0, 1)]
            res = list(ex.map(batch.job, jobs))
            ok = [r for r in res if r['m'] is not None]
            m = sum(r['m'] for r in ok) / max(1, len(ok))
            w = sum(r['m'] > 0 for r in ok)
            rec = dict(cfg=cfg, margin=m, wins=w, n=len(ok), us=sum(r['us'] for r in ok) / max(1, len(ok)),
                       errs=sum(1 for r in res if any(r['err'])), per=[(r['seed'], r['seat'], r['m']) for r in ok])
            with open(out, 'a') as fh:
                fh.write(json.dumps(rec) + '\n')
            print(ci, round(m), w, cfg, flush=True)
            os.remove(path)
