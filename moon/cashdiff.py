"""Mean per-day cash of seat 0 for agents A and B (same opponent, same seeds) and the running difference.
usage: cashdiff.py A B seeds(a-b) [opp]"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
def job(t):
    import lean, decouple
    path, seed, opp = t
    decouple.install(0)
    A = lean.load(path); B = lean.load(opp); cash = {}; ocash = {}
    def wrap(obs, cfg=None):
        s = int(obs['step'])
        if s % 24 == 0: cash[s // 24] = obs['farms'][0]['money']; ocash[s // 24] = obs['farms'][1]['money']
        return A(obs, cfg)
    r = lean.play(None, None, seed, agent_objs=[wrap, B])
    cash[30] = r['r'][0]; ocash[30] = r['r'][1]
    return cash, ocash
if __name__ == '__main__':
    a, b = sys.argv[1], sys.argv[2]; s0, s1 = map(int, sys.argv[3].split('-'))
    opp = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py')
    tot = {p: [collections.Counter(), collections.Counter()] for p in (a, b)}
    with ProcessPoolExecutor(16) as ex:
        for p in (a, b):
            for c, oc in ex.map(job, [(p, s, opp) for s in range(s0, s1 + 1)]):
                tot[p][0].update(c); tot[p][1].update(oc)
    n = s1 - s0 + 1
    print('day   A-us   B-us  diff(us)   A-opp  B-opp diff(opp)  margin-diff')
    for d in range(14, 31):
        au, bu = tot[a][0][d] / n, tot[b][0][d] / n; ao, bo = tot[a][1][d] / n, tot[b][1][d] / n
        print(f"{d:3d} {au:7.0f} {bu:7.0f} {au - bu:+8.0f} {ao:7.0f} {bo:7.0f} {ao - bo:+8.0f}  {(au - ao) - (bu - bo):+8.0f}")
