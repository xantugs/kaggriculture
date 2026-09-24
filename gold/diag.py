"""One closed-loop game; per-day farm census for both seats + deaths + controller telemetry.
usage: diag.py A B seed [days]"""
import sys, os, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
rows = collections.defaultdict(dict)
prev = [None, None]
deaths = collections.defaultdict(collections.Counter)
def census(obs, i):
    c = collections.Counter()
    for row in obs['farms'][i]['tiles']:
        for t in row:
            if t is None: c['empty'] += 1
            elif t == 'LOCKED': pass
            elif t.get('kind') == 'PLANT': c[t['crop'][:4]] += 1
            elif t.get('animal'): c[t['animal'][:4]] += 1
            else: c[t['kind'][:4]] += 1
    return c
def wrap(ag, seat):
    def f(obs, cfg=None):
        a = ag(obs, cfg)
        if obs['hour'] == 0:
            d = obs['day']
            for i in (0, 1):
                cur = obs['farms'][i]['tiles']
                if prev[i] is not None and seat == 0:
                    for y in range(10):
                        for x in range(10):
                            p = prev[i][y][x]; t = cur[y][x]
                            if isinstance(p, dict) and p.get('kind') == 'PLANT' and isinstance(t, dict) and t.get('kind') == 'WEED':
                                deaths[i][p['crop'][:4]] += 1
                            if isinstance(p, dict) and p.get('animal') and isinstance(t, dict) and not t.get('animal'):
                                deaths[i]['esc_' + p['animal'][:4]] += 1
                if seat == 0:
                    prev[i] = json.loads(json.dumps(cur))
                    rows[d][i] = (census(obs, i), int(obs['farms'][i]['money']), dict(deaths[i]))
        return a
    return f
r = lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
print('result', r['r'], 'err', r['err'], 'tmax', r['tmax'])
days = [int(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else range(8, 30)
keys = ['WHEA', 'CARR', 'TOMA', 'STRA', 'MELO', 'GOOS', 'COW', 'SHEE', 'empty', 'WEED', 'COOP', 'PAST']
print('day seat money   ' + ' '.join('%5s' % k for k in keys) + '  deaths(cum)')
for d in days:
    if d not in rows: continue
    for i in (0, 1):
        c, m, de = rows[d][i]
        print('%3d  %d  %7d ' % (d, i, m) + ' '.join('%5d' % c[k] for k in keys) + '  ' + str(de))
tel = getattr(A, 'telemetry', None)
print('telemetry', tel)
