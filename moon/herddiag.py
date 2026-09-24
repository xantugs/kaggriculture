"""Daily own-farm snapshot (animals, crops by type, hands, care/feed done yesterday) for two agents in the same seat/seed.
usage: herddiag.py A B seed [opp]"""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
def run(path, seed, opp):
    decouple.install(0)
    A = lean.load(path); B = lean.load(opp); log = {}; ops = collections.Counter()
    def wrap(obs, cfg=None):
        s = int(obs['step']); act = A(obs, cfg)
        for c in [act.get('farmer') or ['PASS']] + list(act.get('hands') or []):
            if c and c[0] in ('CARE', 'FEED', 'WATER', 'HARVEST', 'FERTILIZE'): ops[(s // 24, c[0])] += 1
        if s % 24 == 23:
            f = obs['farms'][int(obs['player'])]
            an = collections.Counter(t.get('animal') for row in f['tiles'] for t in row if isinstance(t, dict) and t.get('animal'))
            cr = collections.Counter(t.get('crop') for row in f['tiles'] for t in row if isinstance(t, dict) and t.get('kind') == 'PLANT')
            log[s // 24] = (dict(an), dict(cr), len(f['hands']), round(f['money']))
        return act
    r = lean.play(None, None, seed, agent_objs=[wrap, B])
    return r['r'], log, ops
a, b, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]); opp = sys.argv[4] if len(sys.argv) > 4 else '../arena/cand/omw_v15b.py'
ra, la, oa = run(a, seed, opp); rb, lb, ob = run(b, seed, opp)
print(os.path.basename(a), ra, '|', os.path.basename(b), rb)
for d in range(10, 30):
    fa = ' '.join(f"{k[0]}{oa[(d, k)]}" for k in ('CARE', 'FEED', 'WATER', 'HARVEST'))
    fb = ' '.join(f"{k[0]}{ob[(d, k)]}" for k in ('CARE', 'FEED', 'WATER', 'HARVEST'))
    print(d, 'A', la.get(d), fa, '\n   B', lb.get(d), fb)
