"""Trace one tile on one day: which unit plans it, that unit's queue and actions through the day."""
import sys
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); D = int(sys.argv[4]); X, Y = int(sys.argv[5]), int(sys.argv[6])
GC = A.__globals__['_GC']
owner = [None]
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if seat == 0 and obs['day'] == D:
            fm = obs['farms'][0]
            if obs['hour'] == 0:
                for u, r in enumerate(GC.routes):
                    for v in r:
                        if v.pos == (X, Y):
                            owner[0] = u
                            print('planned: unit', u, 'acts', v.acts, 'must', v.must, 'value', round(v.value), 'route len', len(r), 'cost', GC._rcost(GC.spawns[u], r), 'spawn', GC.spawns[u], 'drop_at', GC.drop_at.get(u), file=sys.__stdout__)
                t = fm['tiles'][Y][X]
                print('tile at h0', {k: t.get(k) for k in ('crop','planted_day','consecutive_unwatered','yield_units','watered_today')}, file=sys.__stdout__)
            u = owner[0]
            if u is not None:
                pos = ([fm['farmer']] + fm['hands'])[u] if u < 1 + len(fm['hands']) else None
                act = ([a.get('farmer')] + list(a.get('hands') or []))[u] if pos else None
                q = GC.queues.get(u) or []
                print('h%2d unit %d pos %s act %s next %s' % (obs['hour'], u, pos, act, [(t_, x[0]) for t_, x, _ in q[:3]]), file=sys.__stdout__)
            if obs['hour'] == 23:
                t = fm['tiles'][Y][X]
                print('tile at h23', {k: t.get(k) for k in ('crop','consecutive_unwatered','watered_today')} if isinstance(t, dict) else t, file=sys.__stdout__)
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)], max_steps=24 * (D + 1))
