"""Day 0-2 purchase profile (units, hours) and melon seeding schedule; plus outcome by SW day within each team.
usage: day0.py [old]   old = use the 20-22 Sep seats (stability check) instead of 23-26 Sep"""
import sys, collections
from common import load, by_team, SHORT, TEAMS, pairs, RECENT
from sw_funding import land_event

S = load()
old = len(sys.argv) > 1 and sys.argv[1] == 'old'
if old:
    groups = collections.defaultdict(list)
    for s in S.values():
        if s['role'] == 'rec' and s['date'] not in RECENT:
            groups[s['team']].append(s)
    order = [t for t in TEAMS if groups[t]]
else:
    groups = by_team(S, 'rec')
    groups['T7'] = [p[0] for p in pairs(S)]
    order = TEAMS + ['T7']

print('==== melon seeds bought by day (mean), share of seats with <= 7 melons on day 0; animals d0 by hour ====')
for t in order:
    ss = groups[t]
    mel = [0.0] * 9
    le7 = 0
    hrs = collections.Counter()
    for s in ss:
        for d in range(9):
            x = (s['days'][d].get('buy_seed') or {}).get('MELON')
            if x:
                mel[d] += x[0]
        x0 = (s['days'][0].get('buy_seed') or {}).get('MELON', [0])[0]
        le7 += x0 <= 7
        for h, op, it, n, v in s['days'][0].get('fills') or []:
            if op == 'BA':
                hrs[h] += n
    n = len(ss)
    print('  %-5s melons d0..d8: %s | cum d8 %.1f | d0<=7: %3.0f%% | d0 animals by hour: %s' % (
        SHORT[t], ' '.join('%.1f' % (m / n) for m in mel), sum(mel) / n, 100 * le7 / n,
        ', '.join('h%d:%.1f' % (h, c / n) for h, c in sorted(hrs.items()) if c / n >= 0.1)))

print('\n==== NE / SW / SE timing (share of seats) ====')
for t in order:
    ss = groups[t]
    n = len(ss)
    out = []
    for Q in ('NE', 'SW', 'SE'):
        c = collections.Counter(land_event(s, Q)[0] if land_event(s, Q) else None for s in ss)
        out.append('%s: ' % Q + ' '.join('%s:%d%%' % ('d%d' % k if k is not None else 'none', round(100 * v / n))
                                          for k, v in sorted(c.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)) if v / n >= 0.03))
    print('  %-5s n=%3d  %s' % (SHORT[t], n, ' | '.join(out)))

if not old:
    print('\n==== outcome by SW day within team (recorded games: win rate, mean margin self-other) ====')
    for t in TEAMS:
        ss = groups[t]
        b = collections.defaultdict(list)
        for s in ss:
            ev = land_event(s, 'SW')
            k = 'none' if not ev else ('d%d' % ev[0] if ev[0] <= 9 else 'd10+')
            r = s['seat_row']['rew']
            b[k].append(r[0] - r[1])
        print('  %-5s ' % SHORT[t] + ' | '.join('%s n=%d win %2.0f%% m %+6.0f' % (k, len(v), 100 * sum(x > 0 for x in v) / len(v),
                                                                           sum(v) / len(v)) for k, v in sorted(b.items())))
