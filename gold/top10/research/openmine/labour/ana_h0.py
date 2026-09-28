"""Hour-0 funding of the wage: on seat-days (d1-10) whose hour-0 hires cost more than m0, what is sold at hour 0
(item mix, $), and the hour-0 cash after the list; plus what is planted in the new quadrant on the land days."""
import collections
from common import *

rec, ours, rep = load()
rows = rec + ours
teams = TEAMS + ['T7']
print('== hour-0 sells on seat-days where the hour-0 wage > m0 (days 1-10)')
for t in teams:
    n = 0; items = collections.Counter(); val = 0.0; wage = 0.0; m0 = 0.0
    for r in rows:
        if team_of(r) != t or not (1 <= r['d'] <= 10): continue
        n0 = sum(h == 0 for h in r['hire_h'])
        if fib_sum(n0) <= (r['m0'] or 0): continue
        n += 1; m0 += r['m0']; wage += fib_sum(n0)
        for f in r['fills'] or []:
            if f[0] == 0 and f[1] == 'S':
                items[f[2]] += f[4]; val += f[4]
    if n:
        print('%5s n=%4d  m0 %.0f  h0 wage %.0f  h0 sells $%.0f  mix %s' % (t, n, m0 / n, wage / n, val / n,
              ', '.join('%s %.0f' % (k, v / n) for k, v in items.most_common(5))))

print('\n== crops planted in the new quadrant on its purchase day (mean tiles per seat)')
for Q in ('NE', 'SW'):
    for t in teams:
        c = collections.Counter(); n = 0
        for r in rows:
            if team_of(r) != t or r['d'] > 16: continue
            if not any(e['q'] == Q for e in (r['land'] or [])): continue
            n += 1
            for k, v in (r['ops'] or {}).items():
                if k.startswith('PLANT:') and k.endswith('@' + Q): c[k.split(':')[1].split('@')[0]] += v
                if k.startswith('BUILD') and k.endswith('@' + Q): c[k.split('@')[0]] += v
        if n:
            print('%s %5s n=%3d  %s' % (Q, t, n, ', '.join('%s %.1f' % (k, v / n) for k, v in c.most_common())))
