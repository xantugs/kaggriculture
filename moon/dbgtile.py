"""Follow one tile under a moon build: daily state at hour 0, planned node (acts/prio/route), and unit commands on it."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); seed = int(sys.argv[2]); X, Y = map(int, sys.argv[3].split(',')); D0, D1 = map(int, sys.argv[4].split('-'))
B = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'))
G = A.__globals__; LOG = []
def wrap(obs, cfg=None):
    s = int(obs['step']); d = s // 24; h = s % 24
    a = A(obs, cfg)
    if D0 <= d <= D1:
        f = obs['farms'][int(obs['player'])]; t = f['tiles'][Y][X]
        if h == 0:
            M = G.get('_MOON'); info = []
            for r in getattr(M, 'routes', []) or []:
                for k, nd in enumerate(r.nodes):
                    if tuple(nd.pos) == (X, Y): info.append((r.unit, k, [x[0] for x in nd.acts], nd.prio, round(nd.value)))
            nd = [n for n in getattr(M, "dbg_nodes", []) if n[0] == (X, Y)]; dr = [n for n in getattr(M, "dbg_dropped", []) + getattr(M, "dbg_cut", []) if n[0] == (X, Y)]; M.dbg_cut = []
            LOG.append(f"   nodes={nd} dropped={dr}")
            LOG.append(f"d{d} tile={ {k: t.get(k) for k in ('crop', 'planted_day', 'consecutive_unwatered', 'yield_units', 'watered_today')} if isinstance(t, dict) else t}  planned={info}")
        cmds = [a.get('farmer') or ['PASS']] + list(a.get('hands') or [])
        pos = [f['farmer']] + list(f['hands'])
        for i, (c, p) in enumerate(zip(cmds, pos)):
            if tuple(p) == (X, Y) and c and c[0] not in ('NORTH', 'SOUTH', 'EAST', 'WEST', 'PASS'):
                LOG.append(f"   d{d} h{h} unit {i} does {c}")
    return a
lean.play(None, None, seed, agent_objs=[wrap, B])
print(chr(10).join(LOG))
