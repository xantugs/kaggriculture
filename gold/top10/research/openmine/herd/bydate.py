"""Per team and date: day-0 herd, geese by day 3/7/11, cows by day 3/7, sheep by day 9, SW day; day-0 spend breakdown."""
import collections
from lib import *

rows = load(role={'rec', 'ours'})
G = collections.defaultdict(list)
for r in rows:
    t = SHORT[r['team']] if r['role'] == 'rec' else 'T7'
    G[(t, r['date'])].append(r)


def cum(r, a, D):
    return sum(nbuy(r['days'][d], a) for d in range(D + 1))


def swday(r):
    for day in r['days']:
        for q, h, c in day['land']:
            if q == 'SW':
                return day['d'] + h / 24
    return float('nan')


print('%-5s %-10s %4s | G<=3 G<=7 G<=11 | C<=3 C<=7 C<=11 | S<=5 S<=9 | tot<=11 | SWday | wins' % ('team', 'date', 'n'))
for k in sorted(G):
    rs = G[k]
    w = mean(r['rew'][0] > r['rew'][1] for r in rs if r['rew'])
    print('%-5s %-10s %4d | %4.1f %4.1f %5.1f | %4.1f %4.1f %5.1f | %4.1f %4.1f | %7.1f | %5.2f | %.2f' % (
        k[0], k[1], len(rs), mean(cum(r, 'GOOSE', 3) for r in rs), mean(cum(r, 'GOOSE', 7) for r in rs), mean(cum(r, 'GOOSE', 11) for r in rs),
        mean(cum(r, 'COW', 3) for r in rs), mean(cum(r, 'COW', 7) for r in rs), mean(cum(r, 'COW', 11) for r in rs),
        mean(cum(r, 'SHEEP', 5) for r in rs), mean(cum(r, 'SHEEP', 9) for r in rs),
        mean(sum(cum(r, a, 11) for a in AN) for r in rs), mean(swday(r) for r in rs), w))
