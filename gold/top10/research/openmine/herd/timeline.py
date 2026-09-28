"""Herd timeline per team: owned animals by kind at hour 0 of days 3/6/9/12/16/20, buys per day window,
share of seats buying each kind by day, first-goose day, early cows (denial), structures built by day."""
import sys, collections
from lib import *

rows = load()
groups = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and late(r) and not boey_old(r):
        groups[SHORT[r['team']]].append(r)
    elif r['role'] == 'rec' and r['team'] == 'THIRD FARM CLUB':
        groups['TFC20-22'].append(r)
    elif r['role'] == 'ours':
        groups['T7'].append(r)
    elif r['role'] == 'elite_rep':
        groups['rep:' + SHORT[r['team']]].append(r)
order = ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'TFC20-22', 'T7', 'rep:Boey', 'rep:FQ', 'rep:CBF', 'rep:Yiz', 'rep:TFC']

print('== owned at hour 0 (placed + shed), mean per seat: G/C/S')
DAYS = [2, 3, 4, 6, 9, 10, 12, 16, 20, 25]
print('%-9s %4s ' % ('team', 'n') + ' '.join('%11s' % ('d%d' % d) for d in DAYS))
for g in order:
    rs = groups[g]
    cells = []
    for d in DAYS:
        o = [owned(r['days'][d]) for r in rs]
        cells.append('%3.1f/%3.1f/%3.1f' % tuple(mean(x.get(a, 0) for x in o) for a in AN))
    print('%-9s %4d ' % (g, len(rs)) + ' '.join('%11s' % c for c in cells))

print('\n== animals bought per seat by day window (G/C/S)')
WIN = [(0, 0), (1, 1), (2, 3), (4, 5), (6, 7), (8, 9), (10, 11), (12, 15), (16, 22), (23, 29)]
print('%-9s ' % 'team' + ' '.join('%13s' % ('d%d-%d' % w) for w in WIN))
for g in order:
    rs = groups[g]
    cells = []
    for a0, a1 in WIN:
        cells.append('%3.1f/%3.1f/%3.1f' % tuple(mean(sum(nbuy(r['days'][d], a) for d in range(a0, a1 + 1)) for r in rs) for a in AN))
    print('%-9s ' % g + ' '.join('%13s' % c for c in cells))

print('\n== % seats that bought >=1 of kind by end of day D (G/C/S)')
DD = [0, 1, 3, 5, 7, 9, 11, 15]
print('%-9s ' % 'team' + ' '.join('%12s' % ('<=d%d' % d) for d in DD))
for g in order:
    rs = groups[g]
    cells = []
    for D in DD:
        cells.append('%3.0f/%3.0f/%3.0f' % tuple(pct(sum(nbuy(r['days'][d], a) for d in range(D + 1)) > 0 for r in rs) for a in AN))
    print('%-9s ' % g + ' '.join('%12s' % c for c in cells))

print('\n== total bought days 0-15 and 16-29, and first-buy day median by kind')
for g in order:
    rs = groups[g]
    s = []
    for a in AN:
        t0 = mean(sum(nbuy(r['days'][d], a) for d in range(16)) for r in rs)
        t1 = mean(sum(nbuy(r['days'][d], a) for d in range(16, 30)) for r in rs)
        fd = [min([d for d in range(30) if nbuy(r['days'][d], a)] or [99]) for r in rs]
        fdv = [x for x in fd if x < 99]
        s.append('%s %4.1f+%4.1f first med %s (%3.0f%%)' % (a[0], t0, t1, med(fdv), 100 * len(fdv) / len(rs)))
    print('%-9s ' % g + ' | '.join(s))

print('\n== structures built by window (coops/pastures) and dug')
for g in order:
    rs = groups[g]
    cells = []
    for a0, a1 in [(0, 3), (4, 7), (8, 11), (12, 15), (16, 29)]:
        cells.append('d%d-%d %4.1f/%4.1f' % (a0, a1, mean(sum(r['days'][d]['build_coop'] for d in range(a0, a1 + 1)) for r in rs),
                                            mean(sum(r['days'][d]['build_past'] for d in range(a0, a1 + 1)) for r in rs)))
    dig = mean(sum(r['days'][d]['dig_coop'] + r['days'][d]['dig_past'] for d in range(30)) for r in rs)
    print('%-9s ' % g + '  '.join(cells) + '  dug %.1f' % dig)
