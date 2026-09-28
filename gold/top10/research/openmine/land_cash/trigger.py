"""Trigger test: is the land bought at the first hour the seat can afford it?
For each seat and quadrant Q (price P), rebuild the hourly cash path without the land fill itself and find the first
(day, hour) from day `dmin` on where cash >= P (end of hour, before later purchases). Compare with the actual buy.
Also: T7 'potential' on days 8/9 = m0 + sales - wages - wheat/fertilizer buys (no animal, seed or land purchases),
i.e. what it could hold if it put SW ahead of the herd and seed buys that day."""
import collections
from common import load, by_team, SHORT, TEAMS, pairs
from sw_funding import land_event

S = load()
groups = by_team(S, 'rec')
groups['T7'] = [p[0] for p in pairs(S)]
order = TEAMS + ['T7']
PRICE = {'NE': 1000, 'SW': 2000, 'SE': 4000}
DMIN = {'NE': 5, 'SW': 7, 'SE': 9}


def path(r, skip_land=True, only=None):
    byh = collections.defaultdict(float)
    for h, op, it, n, v in r.get('fills') or []:
        if skip_land and op == 'L':
            continue
        if only is not None and op not in only and not (op == 'BP'):
            continue
        byh[h] += v if op == 'S' else -v
    x = r['m0']; out = []
    for h in range(24):
        x += byh[h]
        out.append(x)
    return out


for Q in ('NE', 'SW', 'SE'):
    print('==== %s ($%d): actual buy vs first affordable hour (from day %d) ====' % (Q, PRICE[Q], DMIN[Q]))
    for t in order:
        ss = groups[t]
        n = same = within3 = later = never = 0
        lag = []
        for s in ss:
            ev = land_event(s, Q)
            if not ev:
                continue
            n += 1
            first = None
            for d in range(DMIN[Q], ev[0] + 1):
                r = s['days'][d]
                c = path(r)
                if r['m0'] >= PRICE[Q]:
                    first = (d, 0); break
                for h in range(24):
                    if c[h] >= PRICE[Q]:
                        first = (d, h); break
                if first:
                    break
            if first is None:
                never += 1
                continue
            L = (ev[0] - first[0]) * 24 + ev[1] - first[1]
            lag.append(L)
            same += L <= 1; within3 += L <= 3; later += L > 24
        if n:
            lag.sort()
            print('  %-5s n=%3d  bought within 1h of first affordable: %3.0f%%, within 3h %3.0f%%, >1 day later %3.0f%%, '
                  'median lag %dh, bought before affordable (cash crossed only in the purchase hour) %d' % (
                      SHORT[t], n, 100 * same / n, 100 * within3 / n, 100 * later / n, lag[len(lag) // 2] if lag else -1, never))
    print()

print('==== T7 potential cash on days 8 and 9 if the day skipped animal/seed buys (sales - wages - wheat/fert buys) ====')
for t in TEAMS:
    L = [p[0] for p in pairs(S) if p[0]['opp'] == t]
    for d in (8, 9):
        pk = []
        hrs = []
        for s in L:
            c = path(s['days'][d], only=('S', 'H'))
            m = max([s['days'][d]['m0']] + c)
            pk.append(m)
            fh = next((h for h in range(24) if c[h] >= 2000), None)
            hrs.append(fh)
        ok = [h for h in hrs if h is not None]
        print('  vs %-5s d%d: potential peak mean %5.0f, >= $2k in %3.0f%% (median first hour %s); actual end cash %5.0f' % (
            SHORT[t], d, sum(pk) / len(pk), 100 * len(ok) / len(L), sorted(ok)[len(ok) // 2] if ok else '-',
            sum(s['days'][d]['mend'] for s in L) / len(L)))
