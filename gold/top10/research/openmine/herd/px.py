"""Median hour-0 prices by day (elite recorded games 23-26 Sep, one row per game) and fertilizer units sold per team."""
import collections
from lib import *
rows = load(role={'rec'})
seen = set()
by = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    if not late(r) or r['gid'] in seen:
        continue
    seen.add(r['gid'])
    for day in r['days'][:17]:
        for k, v in (day.get('px') or {}).items():
            by[day['d']][k].append(v)
print('games', len(seen))
print('day ' + ' '.join('%6s' % k[:5] for k in ('WHEAT', 'EGG', 'MILK', 'WOOL', 'FERTILIZER')))
for d in range(17):
    print('%3d ' % d + ' '.join('%6.0f' % med(by[d][k]) for k in ('WHEAT', 'EGG', 'MILK', 'WOOL', 'FERTILIZER')))
