"""Per-product revenue (us/them) for two candidates on the same pinned games. usage: ledcmp.py candA candB CLASS N"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(t):
    import pinned
    return pinned.job(t)
if __name__ == '__main__':
    a, b, klass, N = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    cls = json.load(open(os.path.join(HERE, 'gameclass.json')))
    files = [f for f in json.load(open(os.path.join(HERE, 'g2800_list.json'))) if (cls.get(os.path.basename(f)[:-5], 0) >= 0.8) == (klass == 'MIRROR')][:N]
    C = os.path.join(HERE, '..', 'arena', 'cand')
    jobs = [(f, 0, 'offhand', os.path.join(C, c + '.py'), 96) for f in files for c in (a, b)]
    agg = {a: [collections.Counter(), collections.Counter()], b: [collections.Counter(), collections.Counter()]}; m = collections.Counter()
    with ProcessPoolExecutor(2) as ex:
        for r in ex.map(job, jobs):
            c = os.path.basename(r['cand'])[:-3]
            agg[c][0].update(r['led_us']); agg[c][1].update(r['led_them']); m[c] += r['m']
    g = len(files)
    print(f'{klass} {g} games: margin {a} {m[a]/g:+.0f}  {b} {m[b]/g:+.0f}')
    keys = sorted(set(agg[a][0]) | set(agg[a][1]) | set(agg[b][0]) | set(agg[b][1]))
    for k in keys:
        print(f'  {k:12s} us {agg[a][0][k]/g:8.0f} -> {agg[b][0][k]/g:8.0f} ({(agg[b][0][k]-agg[a][0][k])/g:+6.0f})   them {agg[a][1][k]/g:8.0f} -> {agg[b][1][k]/g:8.0f} ({(agg[b][1][k]-agg[a][1][k])/g:+6.0f})')
