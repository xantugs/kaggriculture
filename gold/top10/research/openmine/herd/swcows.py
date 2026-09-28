"""SW purchase time vs day-0 cows (and cows by day 1) within each team; day-8 milk units sold."""
import collections
from lib import *
rows = load(role={'rec', 'ours'})
by = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and not late(r):
        continue
    t = SHORT[r['team']] if r['role'] == 'rec' else 'T7'
    c0 = nbuy(r['days'][0], 'COW')
    sw = None
    for day in r['days']:
        for q, h, cb in day['land']:
            if q == 'SW':
                sw = day['d'] + h / 24.0
    m8 = (r['days'][8]['sell'].get('MILK') or [0, 0])
    by[(t, c0)].append((sw if sw is not None else 30, m8[0], m8[1], r['days'][8]['hv'].get('MILK', 0)))
for k in sorted(by):
    v = by[k]
    print('%-5s day0 cows %d: n=%3d SW time mean %.2f (SW by d8 end %.0f%%, by d9 end %.0f%%) | day-8 milk harvested %.1f sold %.1f u $%.0f' % (
        k[0], k[1], len(v), mean(x[0] for x in v), 100 * mean(x[0] < 9 for x in v), 100 * mean(x[0] < 10 for x in v),
        mean(x[3] for x in v), mean(x[1] for x in v), mean(x[2] for x in v)))
