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
    costs = [GC._cost(sp[u], r) for u, r in enumerate(rs)]
    nv = sum(len(r) for r in rs); na = sum(len(v.acts) for r in rs for v in r)
    mv = sum(c for c in costs) - na
    tags = {}
    for r in rs:
        for v in r:
            tags[v.tag] = tags.get(v.tag, 0) + 1
    print('day %2d units %2d visits %3d acts %3d moves+pick %3d costs %s tags %s orders0 %s' % (GC.day, len(rs), nv, na, mv, costs, tags, GC.orders0), file=sys.__stdout__)
GC.plan_day = plan
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'])
print(A.telemetry)
