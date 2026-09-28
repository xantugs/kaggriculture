"""Per-team daily cash-flow statement d0..D (mean $ per seat and day). Net wheat and net fertilizer (sell - buy).
usage: daily.py [D] [paired]   paired: use the recorded elite of the 96 T7 games plus T7 (same towns)"""
import sys, collections
from common import load, by_team, SHORT, TEAMS, pairs

S = load()
D = int(sys.argv[1]) if len(sys.argv) > 1 else 12
paired = len(sys.argv) > 2 and sys.argv[2] == 'paired'
if paired:
    groups = collections.defaultdict(list)
    for t7, e, rep in pairs(S):
        groups[e['team']].append(e)
        groups['T7'].append(t7)
        groups['T7@' + SHORT[e['team']]].append(t7)
    order = TEAMS + ['T7'] + ['T7@' + SHORT[t] for t in TEAMS]
else:
    groups = by_team(S, 'rec')
    groups['T7'] = [p[0] for p in pairs(S)]
    order = TEAMS + ['T7']

COLS = ['m0', 'MILK', 'WOOL', 'EGG', 'MELON', 'STRAW', 'fertN', 'wheatN', 'COW', 'SHEEP', 'GOOSE', 'sMELON', 'sSTRAW',
        'sWHEAT', 'sOTH', 'land', 'wage', 'mend', 'hands']


def row(r):
    c = collections.Counter()
    c['m0'] = r['m0']; c['mend'] = r['mend']; c['hands'] = r.get('hires') or 0
    for it, (n, v) in (r.get('sell') or {}).items():
        k = {'FERTILIZER': 'fertN', 'WHEAT': 'wheatN', 'STRAWBERRY': 'STRAW'}.get(it, it)
        c[k] += v
    for it, (n, v) in (r.get('buy_prod') or {}).items():
        c['fertN' if it == 'FERTILIZER' else 'wheatN'] -= v
    for it, (n, v) in (r.get('buy_animal') or {}).items():
        c[it] -= v
    for it, (n, v) in (r.get('buy_seed') or {}).items():
        c[{'MELON': 'sMELON', 'STRAWBERRY': 'sSTRAW', 'WHEAT': 'sWHEAT'}.get(it, 'sOTH')] -= v
    for L in r.get('land') or []:
        c['land'] -= L['price']
    c['wage'] -= r.get('wage') or 0
    return c


for t in order:
    ss = groups[t]
    if not ss:
        continue
    print('== %s (n=%d)' % (SHORT.get(t, t), len(ss)))
    print('d  ' + ''.join('%7s' % c[:7] for c in COLS))
    for d in range(D + 1):
        tot = collections.Counter()
        for s in ss:
            tot.update(row(s['days'][d]))
        print('%-3d' % d + ''.join('%7.0f' % (tot[c] / len(ss)) if c != 'hands' else '%7.1f' % (tot[c] / len(ss)) for c in COLS))
