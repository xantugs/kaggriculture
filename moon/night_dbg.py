import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena', 'cand', 'omw_v15b.py'))
D = int(sys.argv[2]); LOG = []
def wrap(obs, cfg=None):
    a = A(obs, cfg); s = int(obs['step'])
    if s // 24 == D and s % 24 >= 17:
        pv = obs['private']; shed = sum(pv['shed'].values()); car = sum(sum(i.values()) for i in pv['inventories'])
        LOG.append((s % 24, 'shed', shed, dict(pv['shed']), 'carried', car, 'market', a.get('market')))
    if s // 24 == D + 1 and s % 24 == 0:
        LOG.append(('next day h0 shed', sum(obs['private']['shed'].values()), dict(obs['private']['shed'])))
    return a
lean.play(None, None, 3, agent_objs=[wrap, B])
for l in LOG: print(l)
