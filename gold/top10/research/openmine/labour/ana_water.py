"""Watering coverage by crop: WATER:crop ops (minus same-day plantings of that crop) / crop tiles at hour 0, per team and day.
Also: the FEED/CARE/COLLECT coverage of placed animals, and the per-seat odd/even hire rhythm."""
import collections
from common import *

rec, ours, rep = load()
rows = rec + ours
G = collections.defaultdict(list)
for r in rows:
    G[(team_of(r), r['d'])].append(r)
teams = TEAMS + ['T7']
for crop in ('WHEAT', 'STRAWBERRY', 'MELON', 'TOMATO', 'CARROT'):
    print('\n== WATER coverage %s (%%; tiles in brackets)' % crop)
    print('day ' + ''.join('%13s' % t for t in teams))
    for d in range(1, 17):
        line = '%3d ' % d
        for t in teams:
            rs = G.get((t, d), [])
            w = sum(v for r in rs for k, v in (r['ops'] or {}).items() if k.startswith('WATER:' + crop))
            p = sum(v for r in rs for k, v in (r['ops'] or {}).items() if k.startswith('PLANT:' + crop))
            tl = sum((r['crops'] or {}).get(crop, 0) for r in rs)
            line += '   %4.0f (%4.1f)' % (100 * (w - p) / tl if tl else float('nan'), tl / max(1, len(rs)))
        print(line)

print('\n== animal coverage days 6-16: FEED / CARE / COLLECT_FERTILIZER per placed animal (%), by kind')
for t in teams:
    out = []
    for kind in ('GOOSE', 'COW', 'SHEEP'):
        a = sum((r['herd'] or {}).get(kind, 0) for d in range(6, 17) for r in G.get((t, d), []))
        f = sum(v for d in range(6, 17) for r in G.get((t, d), []) for k, v in (r['ops'] or {}).items() if k.startswith('FEED:' + kind))
        c = sum(v for d in range(6, 17) for r in G.get((t, d), []) for k, v in (r['ops'] or {}).items() if k.startswith('CARE:' + kind))
        cf = sum(v for d in range(6, 17) for r in G.get((t, d), []) for k, v in (r['ops'] or {}).items() if k.startswith('COLLECT_FERTILIZER:' + kind))
        out.append('%s %3.0f/%3.0f/%3.0f' % (kind[:2], 100 * f / max(1, a), 100 * c / max(1, a), 100 * cf / max(1, a)))
    print('%5s  ' % t + '   '.join(out))

print('\n== odd/even rhythm: share of seats with hires(d1)<hires(d0), hires(d7)<min(hires(d6),hires(d8)), hires(d11)<hires(d10)')
S = by_seat(rows)
for t in teams:
    a = b = c = n = 0
    for key, days in S.items():
        if 0 not in days or team_of(days[0]) != t: continue
        if not all(d in days for d in range(12)): continue
        n += 1
        h = [days[d]['hires'] for d in range(12)]
        a += h[1] < h[0]; b += h[7] < min(h[6], h[8]); c += h[11] < h[10]
    print('%5s n=%d  %3.0f%%  %3.0f%%  %3.0f%%' % (t, n, 100 * a / n, 100 * b / n, 100 * c / n))
