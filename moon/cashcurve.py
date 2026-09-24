"""Money at hour 0 of each day for agent A (seat 0) vs B, over seeds (decoupled engine). usage: cashcurve.py A B seeds"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(t):
    import lean, decouple
    a, b, seed = t
    decouple.install(0)
    A = lean.load(a); B = lean.load(b); cash = {}
    def wrap(obs, cfg=None):
        if int(obs['step']) % 24 == 0: cash[int(obs['step']) // 24] = obs['farms'][int(obs['player'])]['money']
        return A(obs, cfg)
    lean.play(None, None, seed, agent_objs=[wrap, B])
    return cash
if __name__ == '__main__':
    a, b = sys.argv[1], sys.argv[2]; s0, s1 = map(int, sys.argv[3].split('-'))
    tot = collections.defaultdict(list)
    with ProcessPoolExecutor(16) as ex:
        for c in ex.map(job, [(a, b, s) for s in range(s0, s1 + 1)]):
            for d, m in c.items(): tot[d].append(m)
    for d in sorted(tot):
        xs = sorted(tot[d]); print(f"day {d:2d}  median {xs[len(xs)//2]:8.0f}  p10 {xs[len(xs)//10]:8.0f}  p90 {xs[9*len(xs)//10]:8.0f}")
