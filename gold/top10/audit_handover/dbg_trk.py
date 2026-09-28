import sys, os, json
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
from pinned4 import reference, install_pinned, _tape, _prefixed
IDX = json.load(open('gold/top10/audit_handover/gid_index.json'))
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
gid = int(sys.argv[1]); lo, hi = int(sys.argv[2]), int(sys.argv[3]); item = sys.argv[4]
d = json.load(open(IDX[str(gid)], encoding='utf-8'))[0]
names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
spawns, shops, _ = reference(d)
orig = install_pinned(12, O, spawns, shops)
A = lean.load('gold/top10/cands/full_au_handover_trk.py'); G = A.__globals__; GC = G['_GC']
LOG = []
inner = _prefixed(A, d['acts'], P, 288)
def f(obs, cfg=None):
    a = inner(obs, cfg); s = int(obs['step'])
    if lo <= s <= hi:
        pv = obs['private']
        LOG.append((s, 'shed', dict(pv['shed']).get(item), 'invs', [dict(i).get(item) for i in pv['inventories']], 'units', [a['farmer']] + a['hands'] if isinstance(a, dict) else a, '\n   mkt', a.get('market'), 'inv', obs['market']['inventory'][item], 'prev.sold', (GC._mk_prev or {}).get('sold'), 'rs', [x for x in GC.rival_sales.get(item, []) if x[0]*24+x[1] >= lo-1]))
    return a
ag = [None, None]; ag[P] = f; ag[O] = _tape(d['acts'], O)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag, max_steps=hi + 2)
for x in LOG: print(*x)
