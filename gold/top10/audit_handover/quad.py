"""Tile census by quadrant at hour 0 of given days (our seat), for a candidate on one live game (S=288).
usage: quad.py cand gid day,day,..."""
import sys, os, json
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed
IDX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gid_index.json')))
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
cand, gid, days = sys.argv[1], int(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')]
d = json.load(open(IDX[str(gid)], encoding='utf-8'))[0]
names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
spawns, shops, _ = reference(d)
orig = install_pinned(12, O, spawns, shops)
A = lean.load(cand); inner = _prefixed(A, d['acts'], P, 288); LOG = []
def f(obs, cfg=None):
    s = int(obs['step'])
    if s % 24 == 0 and s // 24 in days:
        q = {}
        for y, row in enumerate(obs['farms'][P]['tiles']):
            for x, t in enumerate(row):
                qn = ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')
                k = 'empty' if t is None else ('locked' if t == 'LOCKED' else (t.get('crop') or t.get('animal') or t.get('kind')))
                q.setdefault(qn, {}); q[qn][k] = q[qn].get(k, 0) + 1
        LOG.append((s // 24, q, int(obs['farms'][P]['money'])))
    return inner(obs, cfg)
ag = [None, None]; ag[P] = f; ag[O] = _tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=max(days) * 24 + 2)
for x in LOG: print(x)
