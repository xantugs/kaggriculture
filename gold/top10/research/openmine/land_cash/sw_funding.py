"""Where does the $2,000 for SW come from?
(1) per elite seat (23-26 Sep): carry-in cash at hour 0 of the SW day + same-day sales before the purchase by product -
    same-day spending before it; which first harvest coincides (milk day 8 from day-0 cows, wool day 6/9 from day-0 sheep)
(2) T7 in the same towns: hourly cash path days 6-11, first hour with cash >= 2000, and what the tape spends
    the money on between that hour and its own SW buy.
"""
import collections, statistics as st
from common import load, by_team, SHORT, TEAMS, pairs

S = load()


def signed(f):
    h, op, it, n, v = f
    return v if op == 'S' else -v


def hourly(r):
    """end-of-hour cash path from m0 and fills"""
    c = [0.0] * 24
    by_h = collections.defaultdict(float)
    for f in r.get('fills') or []:
        by_h[f[0]] += signed(f)
    x = r['m0']
    for h in range(24):
        x += by_h[h]
        c[h] = x
    return c


def land_event(s, q):
    for d, r in enumerate(s['days']):
        if r is None:
            continue
        for L in r.get('land') or []:
            if L['q'] == q:
                return d, L['h'], L['cash_before']
    return None


def sw_event(s):
    return land_event(s, 'SW')


def label(f):
    h, op, it, n, v = f
    if op == 'S':
        return 'sell:' + it
    if op == 'BP':
        return 'buy:' + it
    if op == 'BA':
        return 'anim:' + it
    if op == 'BS':
        return 'seed'
    if op == 'H':
        return 'wage'
    return 'land:' + it


def funding(groups, order, q='SW'):
    keys = ['m0', 'sell:MILK', 'sell:WOOL', 'sell:FERTILIZER', 'sell:EGG', 'sell:WHEAT', 'buy:WHEAT', 'buy:FERTILIZER',
            'anim:COW', 'anim:SHEEP', 'anim:GOOSE', 'seed', 'wage', 'samehour', 'cash_before']
    print('%-6s %4s %5s ' % ('team', 'n', 'day') + ' '.join('%8s' % k.replace('sell:', 's:').replace('anim:', 'a:')[:8] for k in keys))
    for t in order:
        rows = []
        dd = collections.Counter()
        for s in groups[t]:
            ev = land_event(s, q)
            if not ev:
                continue
            d, hL, cb = ev
            dd[d] += 1
            r = s['days'][d]
            acc = collections.Counter(m0=r['m0'], cash_before=cb)
            before = 0.0
            for f in r.get('fills') or []:
                if f[0] < hL:
                    acc[label(f)] += signed(f)
                    before += signed(f)
            same = 0.0
            for f in r.get('fills') or []:
                if f[0] == hL and f[1] == 'S':
                    acc[label(f)] += f[4]
                    same += f[4]
            acc['samehour'] = cb - r['m0'] - before - same
            rows.append(acc)
        n = len(rows)
        if not n:
            continue
        print('%-6s %4d %5s ' % (SHORT.get(t, t), n, '/'.join('%d' % d for d, _ in dd.most_common(2))) +
              ' '.join('%8.0f' % (sum(a[k] for a in rows) / n) for k in keys))


def part1():
    groups = by_team(S, 'rec')
    groups['T7'] = [s for s in S.values() if s['role'] == 'ours']
    for q in ('NE', 'SW', 'SE'):
        print('(1) %s-day funding (recorded elite 23-26 Sep, T7 96 seats). means over buyers; $ before the purchase hour' % q)
        funding(groups, TEAMS + ['T7'], q)
        print()
    print('share of SW buys preceded the same day (hours <= purchase hour) by: milk sale>=$1k | wool>=$1k | fert>=$500 | carry-in m0>=$2k')
    for t in TEAMS:
        a = b = c = e = n = 0
        for s in groups[t]:
            ev = sw_event(s)
            if not ev:
                continue
            d, hL, cb = ev
            r = s['days'][d]
            sm = collections.Counter()
            for f in r.get('fills') or []:
                if f[0] <= hL and f[1] == 'S':
                    sm[f[2]] += f[4]
            n += 1
            a += sm['MILK'] >= 1000; b += sm['WOOL'] >= 1000; c += sm['FERTILIZER'] >= 500; e += r['m0'] >= 2000
        print('  %-6s n=%3d  milk %3.0f%%  wool %3.0f%%  fert %3.0f%%  m0>=2k %3.0f%%' % (SHORT[t], n, 100 * a / n, 100 * b / n,
                                                                                 100 * c / n, 100 * e / n))


def part2():
    print()
    print('(2) T7 in the same towns: cash path and first moment it could pay $2,000 for SW')
    per = collections.defaultdict(list)
    for s, e, _rep in pairs(S):
        t = SHORT[e['team']]
        evE = sw_event(e)
        first = None
        peaks = {}
        for d in range(6, 12):
            c = hourly(s['days'][d])
            peaks[d] = max([s['days'][d]['m0']] + c)
            if first is None:
                for h in range(24):
                    if c[h] >= 2000 and (d > 6 or h >= 6):
                        first = (d, h)
                        break
        if evE:
            dE, hE, _ = evE
            cE = hourly(s['days'][dE])[hE - 1] if hE > 0 else s['days'][dE]['m0']
        else:
            cE = None
        evO = sw_event(s)
        spend = collections.Counter()
        if first and evO:
            for d in range(first[0], evO[0] + 1):
                for f in s['days'][d].get('fills') or []:
                    if (d, f[0]) <= first or (d, f[0]) >= (evO[0], evO[1]):
                        continue
                    if f[1] != 'S':
                        spend[label(f)] += f[4]
                    else:
                        spend['+' + label(f)] += f[4]
        per[t].append(dict(first=first, peaks=peaks, cE=cE, evE=evE, evO=evO, spend=spend))
    print('%-5s %3s | elite SW t | T7 cash at that hour | T7 first>=2k day (share d8/d9/d10/later) | T7 peak cash d8 d9 d10' % ('opp', 'n'))
    for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC']:
        L = per[t]
        n = len(L)
        tE = [x['evE'][0] + x['evE'][1] / 24 for x in L if x['evE']]
        cE = [x['cE'] for x in L if x['cE'] is not None]
        fd = collections.Counter(x['first'][0] if x['first'] else 99 for x in L)
        print('%-5s %3d | %6.2f     | %8.0f (>=2k %3.0f%%) | d8 %3.0f%% d9 %3.0f%% d10 %3.0f%% later %3.0f%% | %6.0f %6.0f %6.0f' % (
            t, n, st.mean(tE), st.mean(cE), 100 * sum(c >= 2000 for c in cE) / len(cE),
            100 * fd[8] / n, 100 * fd[9] / n, 100 * fd[10] / n, 100 * sum(v for k, v in fd.items() if k > 10 or k < 8) / n,
            st.mean(x['peaks'][8] for x in L), st.mean(x['peaks'][9] for x in L), st.mean(x['peaks'][10] for x in L)))
    allL = [x for L in per.values() for x in L]
    tot = collections.Counter()
    for x in allL:
        tot.update(x['spend'])
    fh = collections.Counter(x['first'] for x in allL)
    print('\nT7 first >=$2k (day,hour) most common:', fh.most_common(6))
    print('T7: flows between its first >=$2k moment and its SW purchase (mean $ per seat, all 96):')
    for k, v in sorted(tot.items(), key=lambda kv: -abs(kv[1])):
        if abs(v) / len(allL) >= 20:
            print('   %-18s %7.0f' % (k, v / len(allL)))


if __name__ == '__main__':
    part1()
    part2()
