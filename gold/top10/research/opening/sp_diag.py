"""sp_diag.py A.py B.py seed [seatA=0] : reacting self-play A vs B on one seed; per-day table of both farms: cash at the
end of the day, the cash gap A-B, hands, revenue estimate per product (units sold x market price at the time), land bought,
plants added, tile census. Shows on which days the gap opens. usage: python sp_diag.py cands/full_OP_p1e.py gold/submit/main_ctl_T8.py 6300 0"""
import sys, os, json, collections
KG = os.getcwd()
sys.path.insert(0, os.path.join(KG, 'arena'))
import lean
pa, pb, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
seatA = int(sys.argv[4]) if len(sys.argv) > 4 else 0
AG = [lean.load(pa), lean.load(pb)]
DAY = [collections.defaultdict(lambda: dict(cash=0, hands=0, rev=collections.Counter(), units=collections.Counter(), land=None, plants=0, places=0, buys=collections.Counter(), census=None, idle=0)) for _ in range(2)]

def census(f):
    c = collections.Counter()
    for row in f['tiles']:
        for t in row:
            if isinstance(t, dict):
                if 'animal' in t: c[t['animal'][0]] += 1
                elif t.get('kind') == 'PLANT': c[t['crop'][0].lower()] += 1
    return c

def mk(side):
    ag = AG[side]
    def w(obs, cfg=None):
        act = ag(obs, cfg)
        st = int(obs['step']); day, hour = divmod(st, 24)
        me = int(obs['player']); farm = obs['farms'][me]; a = DAY[side][day]
        px = obs['market']['prices']
        a['hands'] = max(a['hands'], len(farm['hands']))
        for u in [act.get('farmer') or ['PASS']] + list(act.get('hands') or []):
            if not u or u[0] == 'PASS': a['idle'] += 1
            elif u[0] == 'PLANT': a['plants'] += 1
            elif u[0] == 'PLACE' and len(u) > 1 and u[1] in ('COW', 'SHEEP', 'GOOSE'): a['places'] += 1
        for o in act.get('market') or []:
            if not o: continue
            if o[0] == 'SELL' and len(o) > 2:
                a['units'][o[1]] += int(o[2]); a['rev'][o[1]] += int(o[2]) * float(px.get(o[1], 0) if isinstance(px, dict) else 0)
            elif o[0] == 'BUY_LAND' and a['land'] is None: a['land'] = hour
            elif o[0] in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT') and len(o) > 2: a['buys'][o[1]] += int(o[2])
        if hour == 23:
            a['cash'] = float(farm['money']); a['census'] = census(farm)
        return act
    return w

objs = [None, None]; objs[seatA] = mk(0); objs[1 - seatA] = mk(1)
r = lean.play(None, None, seed, agent_objs=objs)
print('seed %d seatA %d  final A %.0f  B %.0f  (A-B %+.0f)' % (seed, seatA, r['r'][seatA], r['r'][1 - seatA], r['r'][seatA] - r['r'][1 - seatA]))
def rv(c): return ' '.join('%s%d' % (k[:3].lower(), v // 1) for k, v in sorted(c.items(), key=lambda kv: -kv[1]) if v >= 1)[:44]
def cs(c): return ' '.join('%s%d' % (k, v) for k, v in sorted(c.items()) if v)[:30]
print(' d |   A cash   B cash     gap  dgap | hA hB | A revenue (units x price)                    | B revenue                                    | A census                       | B census')
prev = 0
tot = [collections.Counter(), collections.Counter()]
for d in sorted(set(DAY[0]) | set(DAY[1])):
    a, b = DAY[0][d], DAY[1][d]
    gap = a['cash'] - b['cash']
    tot[0].update(a['rev']); tot[1].update(b['rev'])
    print('%2d | %8.0f %8.0f %7.0f %5.0f | %2d %2d | %-44s | %-44s | %-30s | %s' % (d, a['cash'], b['cash'], gap, gap - prev, a['hands'], b['hands'], rv(a['rev']), rv(b['rev']), cs(a['census'] or {}), cs(b['census'] or {})))
    prev = gap
print('revenue totals A: %s' % rv(tot[0])); print('revenue totals B: %s' % rv(tot[1]))
print('revenue A-B by product: %s' % ' '.join('%s%+d' % (k[:3].lower(), tot[0][k] - tot[1][k]) for k in sorted(set(tot[0]) | set(tot[1]), key=lambda k: -(abs(tot[0][k] - tot[1][k])))))
