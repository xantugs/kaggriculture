"""Find animal escapes for seat 0 and show the animal's state on the two days before, plus planned visit and feeds."""
import sys, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
GC = A.__globals__['_GC']
hist = {}
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if seat == 0 and obs['day'] >= 12:
            d = obs['day']; tiles = obs['farms'][0]['tiles']
            if obs['hour'] == 0:
                plan = {}
                for u, r in enumerate(GC.routes):
                    for v in r:
                        if v.tag == 'A': plan[v.pos] = (u, [x[0] for x in v.acts], v.must)
                for y in range(10):
                    for x in range(10):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get('animal'):
                            hist.setdefault((x, y), []).append((d, 'h0', t['animal'], t['consecutive_unfed'], plan.get((x, y)), obs['private']['shed'].get('WHEAT', 0), GC.orders0))
            if obs['hour'] == 23:
                for y in range(10):
                    for x in range(10):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get('animal'):
                            hist[(x, y)].append((d, 'h23', t['animal'], t['fed_today']))
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
for pos, h in hist.items():
    days = [e[0] for e in h if e[1] == 'h0']
    if days and max(days) < 29:
        print('ESCAPED at', pos, 'last seen day', max(days))
        for e in h[-6:]: print('   ', e)
