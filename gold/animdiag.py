"""Animal care audit for seat 0: at hour 23 each day count fed/cared animals; track yields lost to the held cap."""
import sys, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
log = []
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if obs['hour'] in (0, 23) and obs['day'] >= 9:
            for i in (0, 1):
                an = []
                for y, row in enumerate(obs['farms'][i]['tiles']):
                    for x, t in enumerate(row):
                        if isinstance(t, dict) and t.get('animal'):
                            an.append((t['animal'][0], t['fed_today'], t['cared_today'], t['yield_units'], t.get('pending_care_bonus', 0), t['consecutive_unfed']))
                if seat == 0:
                    log.append((obs['day'], obs['hour'], i, an))
        return a
    return f
lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
for d, h, i, an in log:
    if h == 23 and d in (12, 13, 14, 15, 20):
        print('day %d h23 seat %d fed %d/%d cared %d yields %s pend %s unfed %s' % (d, i, sum(a[1] for a in an), len(an), sum(a[2] for a in an), [a[3] for a in an], [a[4] for a in an], [a[5] for a in an]))
    if h == 0 and d in (13, 14, 15, 16, 21):
        print('day %d h0  seat %d yields %s' % (d, i, [(a[0], a[3]) for a in an]))
