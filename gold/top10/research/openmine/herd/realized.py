"""Realized average sell price by day (all elite recorded seats 23-26 Sep + T7) for EGG MILK WOOL FERTILIZER WHEAT, and
wheat buy price. Then an engine-rule ledger: value of one animal bought on day X (fed + cared daily, products sold the
day they appear at that day's realized price, fertilizer sold daily, feed bought at the wheat buy price), by day 16 and 29."""
import collections
from lib import *
rows = load(role={'rec', 'ours'})
S = collections.defaultdict(lambda: [0, 0.0])
B = collections.defaultdict(lambda: [0, 0.0])
for r in rows:
    if r['role'] == 'rec' and not late(r):
        continue
    for day in r['days']:
        for k, (n, usd) in day['sell'].items():
            S[(k, day['d'])][0] += n; S[(k, day['d'])][1] += usd
        for k, (n, usd) in day['bp'].items():
            B[(k, day['d'])][0] += n; B[(k, day['d'])][1] += usd
P = {}
print('day  ' + ' '.join('%6s' % k[:5] for k in ('EGG', 'MILK', 'WOOL', 'FERTILIZER', 'WHEAT')) + '  wheatBuy')
for d in range(30):
    row = []
    for k in ('EGG', 'MILK', 'WOOL', 'FERTILIZER', 'WHEAT'):
        n, usd = S[(k, d)]
        P[(k, d)] = usd / n if n else None
        row.append('%6.0f' % (usd / n) if n else '     -')
    n, usd = B[('WHEAT', d)]
    P[('WB', d)] = usd / n if n else 35
    print('%3d  ' % d + ' '.join(row) + '  %6.1f' % P[('WB', d)])

# fill gaps
for k in ('EGG', 'MILK', 'WOOL', 'FERTILIZER'):
    last = {'EGG': 50, 'MILK': 170, 'WOOL': 205, 'FERTILIZER': 100}[k]
    for d in range(30):
        if P[(k, d)] is None:
            P[(k, d)] = last
        last = P[(k, d)]

A = {'GOOSE': (4, 1, 4, 'EGG', 300), 'COW': (8, 2, 6, 'MILK', 400), 'SHEEP': (6, 3, 6, 'WOOL', 500)}


def ledger(kind, X, end, fert=True):
    fy, iv, mh, prod, cost = A[kind]
    pend = 0; held = 0; val = -cost; units = 0
    for d in range(X, end + 1):
        # day d: fed + cared; products available at hour 0 of day d were produced at end of day d-1
        val -= P[('WB', d)]
        if fert and d > X:
            val += P[('FERTILIZER', d)]
        # end of day d refresh
        nd = d + 1
        dsf = nd - X - fy
        if dsf >= 0 and dsf % iv == 0:
            u = min(mh, 1 + pend)
            pend = 0
            if nd <= end:
                val += u * P[(prod, nd)]
                units += u
        pend += 1
    return val, units


print('\nnet value of one animal bought on day X (fed+cared daily, sold at realized prices, feed at wheat buy price, no labour):')
for kind in AN:
    print(' ', kind, '  '.join('X=%d: d16 %5.0f d29 %5.0f' % ((X,) + (ledger(kind, X, 16)[0], ledger(kind, X, 29)[0])) for X in (0, 2, 4, 6, 9, 11, 13)))
