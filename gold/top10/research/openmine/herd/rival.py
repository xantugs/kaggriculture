"""Do the elite react to the rival's herd? Buys per window split by relevant buyer known x rival's count of that kind at window start."""
import collections
from lib import *
rows = load(role={'rec'})
G = collections.defaultdict(list)
for r in rows:
    if late(r):
        G[SHORT[r['team']]].append(r)
CASES = [('COW', 3, 5, MILKB), ('COW', 6, 9, MILKB), ('SHEEP', 6, 9, YARN), ('GOOSE', 6, 11, EGGB), ('GOOSE', 2, 2, set())]
for kind, a0, a1, buyers in CASES:
    print('==', kind, 'd%d-%d' % (a0, a1), ' split: buyers known (0/1+) x rival %s at start (lo/hi)' % kind)
    for g in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC']:
        rs = G[g]
        riv = [r['days'][a0]['riv_herd'].get(kind, 0) for r in rs]
        thr = med(riv)
        by = collections.defaultdict(list)
        for r, rv in zip(rs, riv):
            b = min(1, sum(1 for s in r['days'][a0]['shops'] if s in buyers))
            by[(b, 'hi' if rv > thr else 'lo')].append(sum(nbuy(r['days'][d], kind) for d in range(a0, a1 + 1)))
        print('  %-5s rival med %.0f  ' % (g, thr) + '  '.join('b%d/%s %.2f (n%d)' % (k[0], k[1], mean(v), len(v)) for k, v in sorted(by.items())))
