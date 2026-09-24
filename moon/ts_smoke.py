import sys; sys.path.insert(0, '../arena')
import lean, decouple
decouple.install(0)
path = sys.argv[1]
for seed in (3, 7):
    A = lean.load(path); B = lean.load('../arena/cand/omw_v15b.py')
    r = lean.play(None, None, seed, agent_objs=[A, B])
    rep = A.__globals__['_M_REPORT']
    print(seed, r['r'], r['err'], r['tmax'], {k: v for k, v in rep.items() if k in ('errors', 'ts_subst', 'planted')})
