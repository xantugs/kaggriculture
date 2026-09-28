"""What goes into SW (and SE) right after purchase: quadrant contents at hour 0 on days after the buy,
and the ops executed in SW on the purchase day and the next two days."""
import collections
from common import load, by_team, SHORT, TEAMS, pairs
from sw_funding import land_event

S = load()
groups = by_team(S, 'rec')
groups['T7'] = [p[0] for p in pairs(S)]
order = TEAMS + ['T7']

for Q in ('SW', 'SE'):
    print('==== %s contents at hour 0, k days after the purchase (mean tiles per buyer) ====' % Q)
    for t in order:
        ss = [s for s in groups[t] if land_event(s, Q)]
        if len(ss) < 5:
            continue
        for k in (1, 2, 3, 5):
            c = collections.Counter(); n = 0
            for s in ss:
                d = land_event(s, Q)[0] + k
                if d > 16:
                    continue
                r = s['days'][d]
                n += 1
                c.update((r.get('q') or {}).get(Q, {}))
            if n:
                print('  %-5s +%dd (n=%3d, day~%.1f): %s' % (SHORT[t], k, n, sum(land_event(s, Q)[0] for s in ss) / len(ss) + k,
                      ', '.join('%s %.1f' % (a, b / n) for a, b in c.most_common() if b / n >= 0.3)))
    print()

print('==== ops in SW, purchase day + next 2 days (mean per buyer) ====')
for t in order:
    ss = [s for s in groups[t] if land_event(s, 'SW')]
    c = collections.Counter()
    for s in ss:
        d0 = land_event(s, 'SW')[0]
        for d in range(d0, min(d0 + 3, 17)):
            for k, v in (s['days'][d].get('ops') or {}).items():
                if k.endswith('@SW') and not k.startswith(('WATER', 'FEED', 'CARE', 'COLLECT', 'HARVEST')):
                    c[k] += v
    print('  %-5s' % SHORT[t], ', '.join('%s %.1f' % (a, b / len(ss)) for a, b in c.most_common(10) if b / len(ss) >= 0.3))
