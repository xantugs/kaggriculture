"""Where do PASS turns happen: by hour and by unit queue state (queue empty vs waiting)."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D = int(sys.argv[4])
GC = A.__globals__['_GC']
byh = collections.Counter(); empty = collections.Counter()
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if seat == 0 and obs['day'] == D:
            units = [a.get('farmer')] + list(a.get('hands') or [])
            for u, x in enumerate(units):
                if x and x[0] == 'PASS':
                    byh[obs['hour']] += 1
                    empty['empty' if not GC.queues.get(u) else 'waiting'] += 1
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)], max_steps=24 * (D + 1))
print('PASS by hour', sorted(byh.items()))
print('queue state', dict(empty))
rs = GC.routes; sp = GC.spawns
print('route costs', [GC._rcost(sp[u], r) for u, r in enumerate(rs)])
