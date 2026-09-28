"""Realized egg / milk / wool price (days 6-15 and 16-29) by the town's final count of buyers of that product."""
import collections
from lib import *
rows = load(role={'rec', 'ours'})
B = {'EGG': EGGB, 'MILK': MILKB, 'WOOL': YARN}
acc = collections.defaultdict(lambda: [0, 0.0])
for r in rows:
    if r['role'] == 'rec' and not late(r):
        continue
    for p, buyers in B.items():
        nb = min(3, sum(1 for s in (r['shops_all'] or []) if s in buyers))
        for day in r['days']:
            v = day['sell'].get(p)
            if not v or day['d'] < 6:
                continue
            w = 'd6-15' if day['d'] <= 15 else 'd16-29'
            acc[(p, nb, w)][0] += v[0]; acc[(p, nb, w)][1] += v[1]
for p in B:
    print(p, '  '.join('buyers%d %s $%.0f (%d u)' % (nb, w, acc[(p, nb, w)][1] / max(1, acc[(p, nb, w)][0]), acc[(p, nb, w)][0])
                       for nb in range(4) for w in ('d6-15', 'd16-29') if acc[(p, nb, w)][0]))
