"""Totals d0-9 and d0-15 per team (per seat means): hires, wage, effective actions, eff per unit-day, moves per eff,
and the per-seat distribution of eff per unit (farmer + hands) by day group."""
import collections
from common import *

rec, ours, rep = load()
S = by_seat(rec + ours)
teams = TEAMS + ['T7']
T = collections.defaultdict(lambda: collections.defaultdict(list))
for key, days in S.items():
    if 0 not in days: continue
    t = team_of(days[0])
    for lo, hi in ((0, 9), (0, 15), (6, 10), (11, 15)):
        rs = [days[d] for d in range(lo, hi + 1) if d in days]
        tag = '%d-%d' % (lo, hi)
        T[t]['hires' + tag].append(sum(r['hires'] for r in rs))
        T[t]['wage' + tag].append(sum(r['wage'] for r in rs))
        L = [labour(r) for r in rs]
        T[t]['eff' + tag].append(sum(x['eff'] for x in L))
        T[t]['units' + tag].append(sum(1 + r['hires'] for r in rs))
        T[t]['move' + tag].append(sum(x['move'] for x in L))
        T[t]['ut' + tag].append(sum(x['ut'] for x in L))
        T[t]['sells' + tag].append(sum(v[1] for r in rs for v in (r['sell'] or {}).values()))
print('team  hires0-9 wage0-9 | hires0-15 wage0-15 | wage/sells0-15 | eff/unit-day 0-9 6-10 11-15 | moves/eff 6-10 11-15')
for t in teams:
    X = T[t]
    e = lambda tag: sum(X['eff' + tag]) / sum(X['units' + tag])
    mv = lambda tag: sum(X['move' + tag]) / sum(X['eff' + tag])
    print('%5s  %6.1f  %6.0f  |  %6.1f  %6.0f  |  %5.1f%%  |  %5.1f %5.1f %5.1f  |  %4.2f %4.2f' % (
        t, mean(X['hires0-9']), mean(X['wage0-9']), mean(X['hires0-15']), mean(X['wage0-15']),
        100 * sum(X['wage0-15']) / sum(X['sells0-15']), e('0-9'), e('6-10'), e('11-15'), mv('6-10'), mv('11-15')))

print('\nper seat-day eff per unit (farmer + hands), days 8-10: p10 / p50 / p90')
G = collections.defaultdict(list)
for key, days in S.items():
    if 0 not in days: continue
    t = team_of(days[0])
    for d in (8, 9, 10):
        r = days.get(d)
        if r: G[t].append(labour(r)['eff'] / (1 + r['hires']))
for t in teams:
    xs = sorted(G[t]); n = len(xs)
    print('%5s  %5.1f %5.1f %5.1f' % (t, xs[n // 10], xs[n // 2], xs[9 * n // 10]))
