"""For seat 0: plants needing water for survival at hour 0 (cu>=1) and whether they were watered by hour 23."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
GC = A.__globals__['_GC']
need = {}
out = []
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if seat == 0 and obs['day'] >= 12:
            tiles = obs['farms'][0]['tiles']
            if obs['hour'] == 0:
                need.clear()
                planned = set()
                for r in GC.routes:
                    for v in r:
                        if any(x[0] == 'WATER' for x in v.acts): planned.add(v.pos)
                for y in range(10):
                    for x in range(10):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get('kind') == 'PLANT' and t['consecutive_unwatered'] >= 1:
                            need[(x, y)] = (t['crop'], (x, y) in planned)
            if obs['hour'] == 23:
                miss = [(p, c, pl) for p, (c, pl) in need.items() if isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get('crop') == c and not tiles[p[1]][p[0]].get('watered_today')]
                out.append((obs['day'], len(need), miss))
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
for d, n, miss in out:
    print('day %d survival-waters %d missed %d %s' % (d, n, len(miss), miss[:6]))
