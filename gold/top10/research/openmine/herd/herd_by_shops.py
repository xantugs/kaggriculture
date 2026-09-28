"""Owned herd at hour 0 of days 6/9/12/16 split by the relevant buyers known that day:
sheep by yarn known (0/1+), cows by milk buyers known (0/1/2+), geese by egg buyers known (0/1/2+)."""
import collections
from lib import *
rows = load(role={'rec', 'ours'})
G = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and late(r) and not boey_old(r):
        G[SHORT[r['team']]].append(r)
    elif r['role'] == 'ours':
        G['T7'].append(r)
SPEC = [('SHEEP', YARN, 1), ('COW', MILKB, 2), ('GOOSE', EGGB, 2)]
for kind, buyers, cap in SPEC:
    print('==', kind, 'owned at h0, by buyers known that day (b0/b1/b2+): mean (n)')
    for g in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
        cells = []
        for d in (6, 9, 12, 16):
            by = collections.defaultdict(list)
            for r in G[g]:
                b = min(cap, sum(1 for s in r['days'][d]['shops'] if s in buyers))
                by[b].append(owned(r['days'][d]).get(kind, 0))
            cells.append('d%-2d ' % d + ' '.join('%4.1f(%3d)' % (mean(by[b]), len(by[b])) if by[b] else '    -     ' for b in range(cap + 1)))
        print('  %-5s ' % g + ' | '.join(cells))
