import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(t):
    fn, cand = t
    import lean, pinned
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(4, O, spawns, shops)
    A = lean.load(os.path.join(HERE, '..', 'arena', 'cand', cand + '.py'))
    ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, 96); ag[O] = pinned._tape(d['acts'], O)
    lean.play(None, None, d['info']['seed'], agent_objs=ag)
    return dict(A.__globals__['_W2S_REPORT'])
if __name__ == '__main__':
    cand = sys.argv[1]; files = json.load(open('g2800_list.json'))[:int(sys.argv[2])]
    tot = collections.Counter(); errs = collections.Counter()
    with ProcessPoolExecutor(15) as ex:
        for r in ex.map(job, [(f, cand) for f in files]):
            for k, v in r.items():
                if isinstance(v, (int, float)): tot[k] += v
                else: errs[v] += 1
    print({k: round(v / len(files), 2) for k, v in tot.items()}); print(errs.most_common(3))
