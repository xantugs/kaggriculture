"""lagdiag.py cand gid seat_of_elite [d1=16] : where does the opening lose its days? Per-day table of our farm vs the
elite's (same town, repaired elite recording in its seat): cash at hour 0 and at the end, hands, idle unit-hours (PASS),
hour of the first sale / land purchase / first PLANT of the day, plants and animals added during the day, seeds still
unplanted and goods still unsold at the end of the day, animals unfed at the end of the day, and the tile census.
usage: python lagdiag.py gold/top10/cands/full_X.py 113065970 1 16"""
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

cand, gid, s = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
d1 = int(sys.argv[4]) if len(sys.argv) > 4 else 16
files = {r['gid']: os.path.join(extract.GAMES, r['file']) for r in extract._index()}
d = extract._load(files[gid])
ref = reference_log(d, s)
rr = dict(hands=ref['hands'], money=ref['money'], outcomes=ref['outcomes'], shops=ref['shops'])
orig_eod = install_town(ref['shops'])
A = lean.load(cand)


def census(f):
    c = collections.Counter()
    for row in f['tiles']:
        for t in row:
            if t is None: c['free'] += 1
            elif t == 'LOCKED': pass
            elif isinstance(t, dict):
                if 'animal' in t:
                    c[t['animal'][0]] += 1
                    if not t.get('fed_today'): c['unfed'] += 1
                elif t.get('kind') == 'PLANT': c[t['crop'][0].lower()] += 1
                elif t.get('kind') == 'WEED': c['weed'] += 1
                else: c['empty_' + t.get('kind', '?')[0]] += 1
    return c


DAY = {}   # day -> dict of accumulators
def acc(day):
    return DAY.setdefault(day, dict(cash0=None, hires=0, idle=0, first_sell={}, land=None, first_plant=None, plants=0,
                                    places=0, sells=collections.Counter(), buys=collections.Counter(), hands_max=0))


def wrapped(obs, cfg=None):
    act = A(obs, cfg)
    st = int(obs['step']); day, hour = divmod(st, 24)
    if day > d1:
        return act
    me = int(obs['player']); farm = obs['farms'][me]
    a = acc(day)
    if hour == 0:
        a['cash0'] = float(farm['money'])
        mel = [t for row in farm['tiles'] for t in row if isinstance(t, dict) and t.get('crop') == 'MELON']
        a['melons0'] = '%dm y%s f%d' % (len(mel), ''.join(str(int(t.get('yield_units', 0))) for t in mel), sum(1 for t in mel if int(t.get('fertilized_until_day', -1)) >= day)) if mel else '-'
        tel = getattr(A, 'telemetry', None) or {}
        a['mfert'] = tel.get('gc_melon_fert', 0); a['liq'] = tel.get('gc_liq_days', 0)
        a['unserved0'] = tel.get('gc_unserved', 0)
        a['census0'] = census(farm); a['elite0'] = census(obs['farms'][1 - me])
        a['seeds0'] = dict(obs['private']['seeds']); a['shed0'] = {k: v for k, v in dict(obs['private']['shed']).items() if v}
    a['hands_max'] = max(a['hands_max'], len(farm['hands']))
    units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
    for u in units:
        if not u or u[0] == 'PASS': a['idle'] += 1
        elif u[0] == 'PLANT':
            a['plants'] += 1
            if a['first_plant'] is None: a['first_plant'] = hour
        elif u[0] == 'PLACE' and len(u) > 1 and u[1] in ('COW', 'SHEEP', 'GOOSE'): a['places'] += 1
    for o in act.get('market') or []:
        if not o: continue
        if o[0] == 'HIRE': a['hires'] += 1
        elif o[0] == 'BUY_LAND' and a['land'] is None: a['land'] = hour
        elif o[0] == 'SELL' and len(o) > 2:
            a['sells'][o[1]] += int(o[2]); a['first_sell'].setdefault(o[1], hour)
        elif o[0] in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_PRODUCT') and len(o) > 2:
            a['buys'][o[1]] += int(o[2])
    if hour == 23:
        a['cash_end'] = float(farm['money']); a['elite_end'] = float(obs['farms'][1 - me]['money'])
        a['unserved'] = (getattr(A, 'telemetry', None) or {}).get('gc_unserved', 0) - a.get('unserved0', 0)
        a['census1'] = census(farm); a['elite1'] = census(obs['farms'][1 - me])
        a['seeds1'] = {k: v for k, v in dict(obs['private']['seeds']).items() if v}
        a['shed1'] = {k: v for k, v in dict(obs['private']['shed']).items() if v}
        a['carried1'] = sum(sum(dict(i).values()) for i in obs['private'].get('inventories') or [])
    return act


try:
    ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); ag[1 - s] = wrapped
    r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
finally:
    K._end_of_day = orig_eod

print('result us %.0f elite %.0f (team %s, shops %s)' % (r['r'][1 - s], r['r'][s], ref.get('team', '?'), rr['shops']))
print(' d | cash0  cashEnd  elite | hnd idle | 1st sell(h)              land  plant(h) n   place | seeds left  unsold shed          carried unfed | us census                          | elite census')
for day in sorted(DAY):
    a = DAY[day]
    fs = ' '.join('%s%d' % (k[:3], h) for k, h in sorted(a['first_sell'].items(), key=lambda kv: kv[1]))[:24]
    def cs(c): return ' '.join('%s%d' % (k, v) for k, v in sorted(c.items()) if k not in ('free',) and v)[:34]
    print('%2d | %-16s mf%2d lq%2d un%5d | %6.0f %7.0f %7.0f | %2d %4d | %-24s %4s  %5s %3d  %5d | %-10s  %-22s %5d  %3d | %-34s | %s' % (
        day, a.get('melons0', '-'), a.get('mfert', 0), a.get('liq', 0), a.get('unserved', 0), a['cash0'] or 0, a.get('cash_end', 0), a.get('elite_end', 0), a['hands_max'], a['idle'], fs,
        ('%d' % a['land']) if a['land'] is not None else '-', ('%d' % a['first_plant']) if a['first_plant'] is not None else '-',
        a['plants'], a['places'], json.dumps({k[:3]: v for k, v in a.get('seeds1', {}).items()}), json.dumps({k[:3]: v for k, v in a.get('shed1', {}).items()}),
        a.get('carried1', 0), a.get('census1', {}).get('unfed', 0), cs(a.get('census1', {})), cs(a.get('elite1', {}))))
