"""Quadrant tile use at hour 0 of days 1,3,5,6,7,9 per team (mean tiles: crops by kind, animals by kind, empty COOP/PASTURE,
weeds, free). Streams the day files (q is on detail rows only)."""
import json, os, collections
from lib import HERE, SHORT
OM = os.path.dirname(HERE)
DAYS = (1, 3, 5, 6, 7, 9, 12)
acc = collections.defaultdict(collections.Counter)
cnt = collections.Counter()
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    with open(os.path.join(OM, fn), encoding='utf-8') as f:
        for l in f:
            r = json.loads(l)
            if r['d'] not in DAYS or (role == 'rec' and r['date'] < '2026-09-23'):
                continue
            t = SHORT[r['team']] if role == 'rec' else 'T7'
            cnt[(t, r['d'])] += 1
            for q, comp in (r.get('q') or {}).items():
                for k, v in comp.items():
                    if isinstance(v, dict):
                        for kk, vv in v.items():
                            acc[(t, r['d'], q)][k + ':' + kk] += vv
                    else:
                        acc[(t, r['d'], q)][k] += v
for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    print('=====', t)
    for d in DAYS:
        n = cnt[(t, d)]
        parts = []
        for q in ('NW', 'NE', 'SW', 'SE'):
            A = acc[(t, d, q)]
            if not A:
                continue
            parts.append('%s[%s]' % (q, ' '.join('%s %.1f' % (k.replace('P:', '').replace('A:', '')[:6], v / n) for k, v in sorted(A.items()) if v / n >= 0.3)))
        print(' d%-2d ' % d + '  '.join(parts))
