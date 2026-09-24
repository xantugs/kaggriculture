"""Action mix for our seat, days 15-28, over the first N pinned games, for several candidates. usage: pinmix.py N cand1,cand2"""
import sys, json, collections
sys.path.insert(0, '.'); sys.path.insert(0, '../arena')
import pinned, lean
from concurrent.futures import ProcessPoolExecutor
def job(t):
    f, i, cand = t
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(f, encoding='utf-8'))[i]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    sp, sh, _ = pinned.reference(d); orig = pinned.install_pinned(15, O, sp, sh)
    C = collections.Counter()
    A = lean.load(cand)
    def w(obs, cfg=None):
        a = A(obs, cfg)
        if 360 <= obs['step'] < 696:
            for u in [a.get('farmer')] + list(a.get('hands') or []):
                op = (u or ['PASS'])[0]
                C['MOVE' if op in ('NORTH', 'SOUTH', 'EAST', 'WEST') else op] += 1
        return a
    ag = [None, None]; ag[P] = pinned._prefixed(w, d['acts'], P, 360); ag[O] = pinned._tape(d['acts'], O)
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    K._end_of_day = orig
    return cand, C, r['r'][P]
if __name__ == '__main__':
    N = int(sys.argv[1]); cands = sys.argv[2].split(',')
    games = [('loss_0922c.json', i) for i in range(16)] + [('loss_0922b.json', i) for i in range(9)]
    jobs = [(f, i, c) for f, i in games[:N] for c in cands]
    tot = {c: collections.Counter() for c in cands}; money = collections.Counter()
    with ProcessPoolExecutor(16) as ex:
        for c, C, m in ex.map(job, jobs):
            tot[c].update(C); money[c] += m
    keys = sorted(set(k for c in cands for k in tot[c]), key=lambda k: -sum(tot[c][k] for c in cands))
    print('money/game', {c: round(money[c] / N) for c in cands})
    for k in keys: print(f"{k:20s}", ' '.join(f"{tot[c][k]/N:8.1f}" for c in cands))
    print('turns', ' '.join(f"{sum(tot[c].values())/N:8.1f}" for c in cands))
