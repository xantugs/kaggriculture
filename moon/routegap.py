"""Planned route end (moon's model) vs actual last non-PASS hour, per unit per day, and counts of planned DROPs."""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); seed = int(sys.argv[2])
B = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'))
G = A.__globals__; planned = {}; last = collections.defaultdict(int); drops = collections.Counter(); LOG = []
def wrap(obs, cfg=None):
    s = int(obs['step']); d = s // 24; h = s % 24
    a = A(obs, cfg)
    M = G.get('_MOON')
    if h == 0 and d >= 15 and M is not None:
        for r in getattr(M, 'routes', []) or []:
            planned[(d, r.unit)] = (r.end(), sum(1 for nd in r.expand() if nd.tag == 'D'), len(r.nodes))
    if d >= 15:
        cmds = [a.get('farmer') or ['PASS']] + list(a.get('hands') or [])
        for i, c in enumerate(cmds):
            if c and c[0] != 'PASS': last[(d, i)] = h
    return a
lean.play(None, None, seed, agent_objs=[wrap, B])
gap = []
for (d, u), (e, nd, nn) in sorted(planned.items()):
    gap.append(e - 1 - last.get((d, u), -1)); drops[d] += nd
import statistics
print('planned end - actual last active hour: mean', round(statistics.mean(gap), 2), 'median', statistics.median(gap), 'n', len(gap))
print('share of routes ending >=3 hours early:', round(sum(g >= 3 for g in gap) / len(gap), 2))
print('planned mid-route DROPs per day:', dict(drops))
