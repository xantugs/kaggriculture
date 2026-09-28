"""Wheat and fertilizer trading: same-hour round trips vs net position, P&L of the round trips, and the physical
balance (harvested / collected, bought, sold, fed / used), days 0..D (default 12)."""
import sys, collections
from common import load, by_team, SHORT, TEAMS, pairs

S = load()
D = int(sys.argv[1]) if len(sys.argv) > 1 else 12
groups = by_team(S, 'rec')
groups['T7'] = [p[0] for p in pairs(S)]
order = TEAMS + ['T7']


def seat_stats(s, item):
    st = collections.Counter()
    for d in range(D + 1):
        r = s['days'][d]
        byh = collections.defaultdict(lambda: [0, 0.0, 0, 0.0])  # bought n,$ sold n,$
        for h, op, it, n, v in r.get('fills') or []:
            if it != item:
                continue
            if op == 'BP':
                byh[h][0] += n; byh[h][1] += v
            elif op == 'S':
                byh[h][2] += n; byh[h][3] += v
        for h, (bn, bv, sn, sv) in byh.items():
            st['buy_n'] += bn; st['buy_$'] += bv; st['sell_n'] += sn; st['sell_$'] += sv
            k = min(bn, sn)
            if k:
                st['rt_n'] += k
                st['rt_pnl'] += k * (sv / sn - bv / bn)
            # one-way remainder
        # cross-day round trips: buy and sell on the same day (any hours)
        dbn = sum(x[0] for x in byh.values()); dsn = sum(x[2] for x in byh.values())
        st['day_rt_n'] += min(dbn, dsn)
        ops = r.get('ops') or {}
        if item == 'WHEAT':
            st['harv'] += (r.get('hv') or {}).get('WHEAT', 0)
            st['fed'] += sum(v for k, v in ops.items() if k.startswith('FEED'))
        else:
            st['harv'] += sum(v for k, v in ops.items() if k.startswith('COLLECT_FERTILIZER'))
            st['fed'] += sum(v for k, v in ops.items() if k.startswith('FERTILIZE:'))
    return st


for item in ('WHEAT', 'FERTILIZER'):
    print('==== %s, days 0-%d, mean per seat ====' % (item, D))
    print('%-5s %7s %7s %7s %7s | %7s %7s %8s | %7s %8s %7s | %6s' % (
        'team', 'buy_n', 'sell_n', 'net_n', 'net_$', 'rt_n', 'dayrt_n', 'rt_pnl', 'harv/col', 'fed/used', 'sold-own', 'share%'))
    for t in order:
        ss = groups[t]
        tot = collections.Counter()
        with_rt = 0
        for s in ss:
            x = seat_stats(s, item)
            tot.update(x)
            with_rt += x['rt_n'] >= 20
        n = len(ss)
        g = {k: v / n for k, v in tot.items()}
        print('%-5s %7.1f %7.1f %7.1f %7.0f | %7.1f %7.1f %8.1f | %7.1f %8.1f %7.1f | %5.0f%%' % (
            SHORT[t], g.get('buy_n', 0), g.get('sell_n', 0), g.get('buy_n', 0) - g.get('sell_n', 0),
            g.get('buy_$', 0) - g.get('sell_$', 0), g.get('rt_n', 0), g.get('day_rt_n', 0), g.get('rt_pnl', 0),
            g.get('harv', 0), g.get('fed', 0), g.get('sell_n', 0) - g.get('day_rt_n', 0), 100 * with_rt / n))
    print('  rt_n = units bought and sold in the same hour; dayrt_n = same day; rt_pnl = $ made on the same-hour round trips;')
    print('  share% = seats with >= 20 same-hour round-trip units')
    print()
