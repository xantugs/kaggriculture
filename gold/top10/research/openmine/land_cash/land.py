"""Land purchase timing and cash at purchase, per team (23-26 Sep recorded elite) and T7 (ours, 96 seats)."""
import collections, statistics as st
from common import load, by_team, SHORT, TEAMS

S = load()


def q(xs, p):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    k = (len(xs) - 1) * p
    i = int(k)
    return xs[i] if i + 1 >= len(xs) else xs[i] + (xs[i + 1] - xs[i]) * (k - i)


def land_ev(s):
    ev = {}
    for d, r in enumerate(s['days']):
        if r is None:
            continue
        for L in r.get('land') or []:
            ev[L['q']] = dict(d=d, h=L['h'], t=d + L['h'] / 24, cash=L['cash_before'])
    return ev


groups = by_team(S, 'rec')
groups['T7'] = [s for s in S.values() if s['role'] == 'ours']
groups['rep(T7 games)'] = [s for s in S.values() if s['role'] == 'elite_rep']
order = TEAMS + ['T7', 'rep(T7 games)']
for quad in ('NE', 'SW', 'SE'):
    print('==', quad)
    print('%-16s %4s %6s %6s %6s %6s | %5s %5s %5s  | cash_before p25/med/p75 | day histogram' % (
        'team', 'n', 'have%', 'p25', 'med', 'p75', 'h_med', 'h<6%', '', ))
    for t in order:
        ss = groups[t]
        evs = [land_ev(s).get(quad) for s in ss]
        got = [e for e in evs if e]
        if not ss:
            continue
        ts = [e['t'] for e in got]
        hs = [e['h'] for e in got]
        cs = [e['cash'] for e in got]
        hist = collections.Counter(e['d'] for e in got)
        hs_txt = ' '.join('d%d:%d' % (d, round(100 * n / len(ss))) for d, n in sorted(hist.items()) if n / len(ss) >= 0.03)
        print('%-16s %4d %5.0f%% %6.2f %6.2f %6.2f | %5.1f %4.0f%%       | %6.0f %6.0f %6.0f | %s' % (
            SHORT.get(t, t), len(ss), 100 * len(got) / len(ss), q(ts, .25), q(ts, .5), q(ts, .75),
            q(hs, .5) if hs else float('nan'), 100 * sum(h < 6 for h in hs) / max(1, len(hs)),
            q(cs, .25), q(cs, .5), q(cs, .75), hs_txt))
