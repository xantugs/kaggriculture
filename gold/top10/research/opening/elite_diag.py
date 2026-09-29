"""elite_diag.py cand gid seat_of_elite : cand vs the repaired elite recording in the elite's town (lagdiag setup); per-day
cash of both, the gap, revenue by product (units x price at order time) for both, tile census for both. Shows where the
elite's money comes from by day. usage: python elite_diag.py gold/submit/main_ctl_T8.py 113065970 1"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
OM = os.path.join(os.path.dirname(HERE), 'openmine')
KG = os.path.normpath(os.path.join(OM, '..', '..', '..', '..'))
sys.path.insert(0, OM)
for p in ('arena', 'gold/harness', 'gold/elite'):
    sys.path.insert(0, os.path.join(KG, p))
import lean, extract
from eval_elite_routes import install_town
from transplant import build_agent, reference_log
from kaggle_environments.envs.kaggriculture import kaggriculture as K

cand = sys.argv[1]
if ':' in sys.argv[2]:
    # live game from a livefetch file: FILE.jsonl:GID ; the rival is the seat we did not play (seat arg ignored)
    fn, gid = sys.argv[2].rsplit(':', 1); gid = int(gid)
    d = [json.loads(l) for l in open(fn, encoding='utf-8') if l.startswith('{') and json.loads(l)['id'] == gid][0]
    s = 1 - int(d['meta']['seat'])
else:
    gid, s = int(sys.argv[2]), int(sys.argv[3])
    files = {r['gid']: os.path.join(extract.GAMES, r['file']) for r in extract._index()}
    d = extract._load(files[gid])
ref = reference_log(d, s)
rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
orig_eod = install_town(ref['shops'])
EL = build_agent(d['acts'], s, rr, slack_min=20)
if cand == 'REC':
    ref2 = reference_log(d, 1 - s)
    rr2 = dict(hands=ref2['hands'], money=ref2['money'], outcomes=ref2['outcomes'], shops=ref2['shops'])
    A = build_agent(d['acts'], 1 - s, rr2, slack_min=20)
else:
    A = lean.load(cand)
SIG = {}
DAY = [collections.defaultdict(lambda: dict(cash=0, hands=0, rev=collections.Counter(), units=collections.Counter(), land=None, plants=0, places=0, census=None, idle=0, feed=0, buyw=0, buyf=0, px={}, inv={})) for _ in range(2)]

def census(f):
    c = collections.Counter()
    for row in f['tiles']:
        for t in row:
            if isinstance(t, dict):
                if 'animal' in t: c[t['animal'][0]] += 1
                elif t.get('kind') == 'PLANT': c[t['crop'][0].lower()] += 1
    return c

def mk(side, ag):
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
            elif o[0] == 'BUY_PRODUCT' and len(o) > 2 and o[1] == 'WHEAT': a['buyw'] += int(o[2]); a['rev']['WHEAT'] -= int(o[2]) * float(px.get('WHEAT', 0))
            elif o[0] == 'BUY_PRODUCT' and len(o) > 2 and o[1] == 'FERTILIZER': a['buyf'] += int(o[2]); a['rev']['FERTILIZER'] -= int(o[2]) * float(px.get('FERTILIZER', 0))
        for u in [act.get('farmer') or ['PASS']] + list(act.get('hands') or []):
            if u and u[0] == 'FEED': a['feed'] += 1
        if st == 1 and side == 0:
            rf = obs['farms'][1 - me]; SIG['m'] = float(rf['money']); SIG['h'] = len(rf['hands'])
        if hour == 12:
            inv = obs['market']['inventory']
            a['px'] = {k: float(px[k]) for k in ('WHEAT', 'STRAWBERRY', 'FERTILIZER', 'MILK', 'WOOL', 'MELON')}
            a['inv'] = {k: int(inv[k]) - 10000 for k in ('WHEAT', 'STRAWBERRY', 'FERTILIZER', 'MILK', 'WOOL', 'MELON')}
        if hour == 23:
            a['cash'] = float(farm['money']); a['census'] = census(farm)
        return act
    return w

try:
    ag = [None, None]; ag[s] = mk(1, EL); ag[1 - s] = mk(0, A)
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
finally:
    K._end_of_day = orig_eod
print('gid %d seat %d team %s shops %s: us %.0f elite %.0f (us-elite %+.0f)  rival step1 money %s hands %s' % (gid, s, ref.get('team', '?'), rr['shops'], r['r'][1 - s], r['r'][s], r['r'][1 - s] - r['r'][s], SIG.get('m'), SIG.get('h')))
def rv(c): return ' '.join('%s%d' % (k[:3].lower(), v // 1) for k, v in sorted(c.items(), key=lambda kv: -abs(kv[1])) if abs(v) >= 1)[:46]
def cs(c): return ' '.join('%s%d' % (k, v) for k, v in sorted(c.items()) if v)[:30]
print(' d |  us cash  el cash     gap  dgap | hU hE | us revenue                                     | elite revenue                                  | us census                      | elite census')
prev = 0; tot = [collections.Counter(), collections.Counter()]
for day in sorted(set(DAY[0]) | set(DAY[1])):
    a, b = DAY[0][day], DAY[1][day]; gap = a['cash'] - b['cash']
    tot[0].update(a['rev']); tot[1].update(b['rev'])
    print('%2d | %8.0f %8.0f %7.0f %5.0f | %2d %2d | %-46s | %-46s | %-30s | %s' % (day, a['cash'], b['cash'], gap, gap - prev, a['hands'], b['hands'], rv(a['rev']), rv(b['rev']), cs(a['census'] or {}), cs(b['census'] or {})))
    prev = gap
print('MARKET at hour 12 (price / inventory-10000):')
print(' d | wheat        straw        fert         milk         wool         melon      | us units sold                          feed buyW buyF | elite units sold                       feed buyW buyF')
for day in sorted(set(DAY[0]) | set(DAY[1])):
    a, b = DAY[0][day], DAY[1][day]
    if not a['px']: continue
    print('%2d | %s | %-38s %4d %4d %4d | %-38s %4d %4d %4d' % (day, ' '.join('%4.0f/%-7d' % (a['px'][k], a['inv'][k]) for k in ('WHEAT', 'STRAWBERRY', 'FERTILIZER', 'MILK', 'WOOL', 'MELON')), rv(a['units'])[:38], a['feed'], a['buyw'], a['buyf'], rv(b['units'])[:38], b['feed'], b['buyw'], b['buyf']))
print('NET (sales - wheat/fert purchases) totals us   : %s' % rv(tot[0])); print('NET totals elite: %s' % rv(tot[1]))
print('revenue us-elite by product: %s' % ' '.join('%s%+d' % (k[:3].lower(), tot[0][k] - tot[1][k]) for k in sorted(set(tot[0]) | set(tot[1]), key=lambda k: -(abs(tot[0][k] - tot[1][k])))))
