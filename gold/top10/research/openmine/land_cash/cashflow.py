"""Day 0..12 cash-flow statement per team (recorded elite, 23-26 Sep) next to T7 in the same towns.
usage: cashflow.py [D1,D2,...]   cumulative through the end of those days (default 5,8,12)
Also: paired table T7 vs the recorded elite of the same 96 games.
"""
import sys, collections
from common import load, by_team, SHORT, TEAMS, pairs

S = load()
DAYS = [int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else '5,8,12').split(',')]


def flows(r):
    f = collections.Counter()
    for it, (n, v) in (r.get('sell') or {}).items():
        f['+sell:' + it] += v
    for it, (n, v) in (r.get('buy_seed') or {}).items():
        f['-seed:' + it] -= v
    for it, (n, v) in (r.get('buy_animal') or {}).items():
        f['-anim:' + it] -= v
    for it, (n, v) in (r.get('buy_prod') or {}).items():
        f['-buy:' + it] -= v
    for L in r.get('land') or []:
        f['-land:' + L['q']] -= L['price']
    f['-wage'] -= r.get('wage') or 0
    return f


def units(r):
    f = collections.Counter()
    for k, key in (('sell', 'sell'), ('buy_prod', 'buy'), ('buy_seed', 'seed'), ('buy_animal', 'anim')):
        for it, (n, v) in (r.get(k) or {}).items():
            f[key + ':' + it] += n
    return f


def cum(s, D, fn=flows):
    c = collections.Counter()
    for d in range(D + 1):
        r = s['days'][d]
        if r:
            c.update(fn(r))
    return c


def table(groups, order, D, fn=flows, fmt='%7.0f'):
    allk = set()
    means = {}
    for t in order:
        ss = groups[t]
        tot = collections.Counter()
        for s in ss:
            tot.update(cum(s, D, fn))
        means[t] = {k: v / len(ss) for k, v in tot.items()}
        allk |= set(tot)
    keys = sorted(allk, key=lambda k: (k[0] == '-', k))
    print('%-18s' % ('thru d%d' % D) + ''.join('%8s' % SHORT.get(t, t)[:8] for t in order))
    tin = {t: 0 for t in order}; tout = {t: 0 for t in order}
    for k in keys:
        vals = [means[t].get(k, 0) for t in order]
        if max(abs(v) for v in vals) < (20 if fn is flows else 0.5):
            for t, v in zip(order, vals):
                (tin if v > 0 else tout)[t] += v
            continue
        for t, v in zip(order, vals):
            (tin if v > 0 else tout)[t] += v
        print('%-18s' % k + ''.join((' ' + fmt) % v for v in vals))
    if fn is flows:
        print('%-18s' % 'IN total' + ''.join(' %7.0f' % tin[t] for t in order))
        print('%-18s' % 'OUT total' + ''.join(' %7.0f' % tout[t] for t in order))
        end = {t: sum(s['days'][D]['mend'] for s in groups[t]) / len(groups[t]) for t in order}
        print('%-18s' % 'cash end' + ''.join(' %7.0f' % end[t] for t in order))
    print()


if __name__ == '__main__':
    groups = by_team(S, 'rec')
    ours = [s for s in S.values() if s['role'] == 'ours']
    groups['T7'] = ours
    order = TEAMS + ['T7']
    for D in DAYS:
        table(groups, order, D)
    print('#### units, thru d8')
    table(groups, order, 8, units, '%7.1f')
    # paired: T7 vs recorded elite in the same game
    pg = collections.defaultdict(list)
    for s, e, _rep in pairs(S):
        pg['E:' + SHORT[e['team']]].append(e)
        pg['T7:' + SHORT[e['team']]].append(s)
    po = []
    for t in TEAMS:
        po += ['E:' + SHORT[t], 'T7:' + SHORT[t]]
    print('#### paired same towns (recorded elite E vs T7)')
    for D in DAYS:
        table(pg, po, D)
