"""Audit the controller's daily plans: visits, actions, route costs per unit, unserved, fert/wheat needs."""
import sys, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
path = sys.argv[1]; opp = sys.argv[2]; seed = int(sys.argv[3])
A = lean.load(path); B = lean.load(opp)
g = A.__globals__
GC = g['_GC']
orig = GC.plan_day
def plan(obs):
    orig(obs)
    rs = GC.routes; sp = GC.spawns
    costs = [GC._rcost(sp[u], r) for u, r in enumerate(rs)]
    nv = sum(len(r) for r in rs); na = sum(len(v.acts) for r in rs for v in r)
    mv = sum(c for c in costs) - na
    tags = {}
    for r in rs:
        for v in r:
            tags[v.tag] = tags.get(v.tag, 0) + 1
    import collections as _c
    allv = GC._last_visits if hasattr(GC, '_last_visits') else []
    print('day %2d units %2d visits %3d acts %3d moves+pick %3d costs %s tags %s unserved_must %s' % (GC.day, len(rs), nv, na, mv, costs, tags, getattr(GC, '_last_unserved', None)), file=sys.__stdout__)
GC.plan_day = plan
sys.path.insert(0, '/home/user/kaggriculture/arena')
import decouple
decouple.install(0)
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'])
print(A.telemetry)
