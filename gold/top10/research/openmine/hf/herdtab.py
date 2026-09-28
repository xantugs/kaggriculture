import json, collections, sys
sys.path.insert(0, 'herd')
from lib import *
MB = MILKB; EB = EGGB
rows = [r for r in load(role=('rec',)) if late(r) and r['team'] in ('Boey', 'Fourth Quadrant', 'THIRD FARM CLUB') and not boey_old(r)]
print(len(rows), collections.Counter(SHORT[r['team']] for r in rows))
def nb(shops, S): return sum(1 for s in shops if s in S)
for team in ('Boey', 'Fourth Quadrant', 'THIRD FARM CLUB'):
    R = [r for r in rows if r['team'] == team]
    print('==', team, len(R))
    for an, S, lab in (('COW', MB, 'milk'), ('SHEEP', YARN, 'yarn'), ('GOOSE', EB, 'egg')):
        print(' ', an, 'owned at hour 0 of day d (incl shed) by #', lab, 'buyers known that day')
        for d in list(range(0, 17)):
            by = collections.defaultdict(list)
            for r in R:
                D = r['days'][d]
                k = min(2, nb(D['shops'], S))
                by[k].append(owned(D).get(an, 0) + (D['ba'].get(an, [0])[0]))
            print('   d%2d ' % d + '  '.join('%d:%5.2f(n%3d)' % (k, mean(v), len(v)) for k, v in sorted(by.items())))
