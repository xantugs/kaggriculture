"""Animal buy events: day, hour, cash at the observation, shops known, quads; per team and kind.
Prints distributions of (day,hour) and cash-before for each (team, kind, day-window)."""
import collections, sys
from lib import *

rows = load(role={'rec', 'ours'})
ev = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and not late(r):
        continue
    t = SHORT[r['team']] if r['role'] == 'rec' else 'T7'
    for day in r['days']:
        for h, item, n, usd, cash in day.get('ba_fills', []):
            ev[(t, item)].append(dict(gid=r['gid'], d=day['d'], h=h, n=n, cash=cash, shops=day['shops'], quads=day['quads']))

for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    print('=====', t)
    for a in AN:
        es = ev[(t, a)]
        if not es:
            continue
        byd = collections.defaultdict(list)
        for e in es:
            byd[e['d']].append(e)
        parts = []
        for d in sorted(byd):
            xs = byd[d]
            hs = collections.Counter(e['h'] for e in xs).most_common(3)
            parts.append('d%d: %d ev %d u, h%s, cash med %.0f' % (d, len(xs), sum(e['n'] for e in xs),
                         '/'.join('%d:%d' % hc for hc in hs), med(e['cash'] for e in xs)))
        print(' ', a)
        for p in parts:
            print('    ' + p)
