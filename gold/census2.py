"""Tile census at hour H of each day, both seats, averaged over seeds (decoupled).
usage: census2.py A.py B.py seeds [H]"""
import sys, collections, multiprocessing as mp
sys.path.insert(0, '/home/user/kaggriculture/arena')

def kind(t):
    if t is None: return 'empty'
    if t == 'LOCKED': return None
    if isinstance(t, dict):
        if 'animal' in t: return t['animal'] if isinstance(t['animal'], str) else t['animal'].get('type', 'ANIM')
        if 'crop' in t: return t['crop'] if isinstance(t['crop'], str) else t['crop'].get('type', 'CROP')
        return t.get('kind', '?')
    return str(t)

def run(args):
    A0, B0, seed, H = args
    import lean, decouple
    decouple.install(0)
    A = lean.load(A0); B = lean.load(B0)
    C = collections.defaultdict(collections.Counter)
    def wrap(ag, seat):
        def f(obs, cfg=None):
            if seat == 0 and obs['hour'] == H:
                for i in range(2):
                    for row in obs['farms'][i]['tiles']:
                        for t in row:
                            k = kind(t)
                            if k: C[(obs['day'], i)][k] += 1
            return ag(obs, cfg)
        return f
    lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
    return {k: dict(v) for k, v in C.items()}

if __name__ == '__main__':
    A0, B0 = sys.argv[1], sys.argv[2]
    s = sys.argv[3]
    seeds = list(range(int(s.split('-')[0]), int(s.split('-')[1]) + 1)) if '-' in s else [int(x) for x in s.split(',')]
    H = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    with mp.Pool(4) as p:
        res = p.map(run, [(A0, B0, sd, H) for sd in seeds])
    T = collections.defaultdict(collections.Counter)
    for r in res:
        for k, v in r.items(): T[k].update(v)
    n = len(res)
    kinds = sorted(set(k for v in T.values() for k in v))
    print('day seat ' + ' '.join('%6s' % k[:6] for k in kinds))
    for d in range(8, 30):
        for i in range(2):
            print('%3d %4s ' % (d, 'A' if i == 0 else 'B') + ' '.join('%6.1f' % (T[(d, i)][k] / n) for k in kinds))
    print('tile-days d12-29:')
    for i in range(2):
        tot = collections.Counter()
        for d in range(12, 30): tot.update(T[(d, i)])
        print('A' if i == 0 else 'B', ' '.join('%s=%.0f' % (k, tot[k] / n) for k in kinds))
