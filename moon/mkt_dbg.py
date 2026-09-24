import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena', 'cand', 'omw_v15b.py'))
D = int(sys.argv[2]); LOG = []
def wrap(obs, cfg=None):
    a = A(obs, cfg); s = int(obs['step'])
    if (s // 24 == D and s % 24 <= 2) or (s // 24 == D - 1 and s % 24 >= 20):
        f = obs['farms'][int(obs['player'])]
        LOG.append((s % 24, 'fert', obs['private']['shed'].get('FERTILIZER', 0), 'wheat', obs['private']['shed'].get('WHEAT', 0), 'shed', sum(obs['private']['shed'].values()), a.get('market')))
    return a
lean.play(None, None, int(sys.argv[3]) if len(sys.argv) > 3 else 3, agent_objs=[wrap, B])
for l in LOG: print(l)
