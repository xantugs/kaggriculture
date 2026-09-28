"""Animal buys per window conditional on shops known at the window start: yarn store known (Y/-),
milk buyers known (m0/m1/m2+), egg buyers known (e0/e1+). Mean units per seat and % seats buying >=1."""
import collections, sys
from lib import *

rows = load(role={'rec', 'ours'})
G = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and late(r) and not boey_old(r):
        G[SHORT[r['team']]].append(r)
    elif r['role'] == 'ours':
        G['T7'].append(r)
WIN = [(3, 5), (6, 7), (8, 9), (10, 11), (12, 15), (16, 29)]


def ctx(day, kind):
    s = day['shops']
    if kind == 'GOOSE':
        n = sum(1 for x in s if x in EGGB)
        return 'egg%d' % min(n, 2)
    if kind == 'COW':
        n = sum(1 for x in s if x in MILKB)
        return 'milk%d' % min(n, 2)
    if kind == 'SHEEP':
        n = sum(1 for x in s if x in YARN)
        return 'yarn%d' % min(n, 1)


for kind in AN:
    print('=========', kind, ' (units per seat | %% seats buying) by window, split by relevant buyers known at window start')
    for g in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
        rs = G[g]
        line = []
        for a0, a1 in WIN:
            byc = collections.defaultdict(list)
            for r in rs:
                c = ctx(r['days'][a0], kind)
                byc[c].append(sum(nbuy(r['days'][d], kind) for d in range(a0, a1 + 1)))
            line.append('d%d-%d ' % (a0, a1) + ' '.join('%s:%.1f|%.0f%%(n%d)' % (c, mean(v), pct(x > 0 for x in v), len(v)) for c, v in sorted(byc.items())))
        print('--', g)
        for l in line:
            print('    ' + l)
