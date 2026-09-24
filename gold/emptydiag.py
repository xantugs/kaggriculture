"""Seat 0: at hour 0 list empty/weed tiles, whether today's plan has a PLANT/DIG visit for them, and seed stock."""
import sys
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
GC = A.__globals__['_GC']
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if seat == 0 and obs['hour'] == 0 and obs['day'] >= 12:
            tiles = obs['farms'][0]['tiles']
            planned = {}
            for r in GC.routes:
                for v in r:
                    if any(x[0] in ('PLANT', 'DIG') for x in v.acts): planned[v.pos] = [x[0] for x in v.acts]
            em = [(x, y) for y in range(10) for x in range(10) if tiles[y][x] is None]
            we = [(x, y) for y in range(10) for x in range(10) if isinstance(tiles[y][x], dict) and tiles[y][x].get('kind') == 'WEED']
            print('day %d empty %d (planned %d) weeds %d (planned %d) seeds %s orders1 %s' % (obs['day'], len(em), sum(p in planned for p in em), len(we), sum(p in planned for p in we), dict((k, v) for k, v in obs['private']['seeds'].items() if v), GC.orders1), file=sys.__stdout__)
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
