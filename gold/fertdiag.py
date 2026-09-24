"""Per day (seat 0): strawberry eves needing fertilizer, planned FERTILIZE visits, executed FERTILIZE, fert in shed at h0."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
GC = A.__globals__['_GC']
rows = []
cur = {}
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if seat == 0 and obs['day'] >= 12:
            d = obs['day']; tiles = obs['farms'][0]['tiles']
            if obs['hour'] == 0:
                eves = 0
                for y in range(10):
                    for x in range(10):
                        t = tiles[y][x]
                        if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY':
                            age = d - t['planted_day']; k = age + 1 - 10
                            if k >= 0 and k % 2 == 0 and k // 2 + 1 <= 4 and t['fertilized_until_day'] < d:
                                eves += 1
                planned = sum(1 for r in GC.routes for v in r if v.fert and any(x[0] == 'FERTILIZE' for x in v.acts))
                pl_s = sum(1 for r in GC.routes for v in r if v.fert and v.tag == 'O')
                cur.clear(); cur.update(d=d, eves=eves, planned=planned, pl_straw=pl_s, shed=obs['private']['shed'].get('FERTILIZER', 0), exe=0, orders0=list(GC.orders0))
                rows.append(cur.copy())
            units = [a.get('farmer')] + list(a.get('hands') or [])
            rows[-1]['exe'] = rows[-1].get('exe', 0) + sum(1 for x in units if x and x[0] == 'FERTILIZE')
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
for r in rows:
    print(r)
