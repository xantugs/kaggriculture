"""Per-seat consistency (% of seats) of the candidate labour rules, per team, and T7 in the same towns.
usage: ana_rules.py            (elite 23-26 Sep all seats; T7 96 seats)
       ana_rules.py T7pair     (elite restricted to the recorded seats of the 96 T7 games)"""
import sys, collections
from common import *

rec, ours, rep = load()
if len(sys.argv) > 1 and sys.argv[1] == 'T7pair':
    keys = {(r['gid'], r['opp']) for r in ours}
    rec = [r for r in rec if (r['gid'], r['team']) in keys]
S = by_seat(rec + ours)
teams = TEAMS + ['T7']


def landday(days, Q):
    for d in range(17):
        r = days.get(d)
        if r is None: continue
        for e in r['land'] or []:
            if e['q'] == Q: return d, e
    return None, None


RULES = collections.OrderedDict()


def rule(name):
    def deco(fn):
        RULES[name] = fn
        return fn
    return deco


@rule('d2-5 hires >= 5 every day')
def _(days): return all(days[d]['hires'] >= 5 for d in range(2, 6))


@rule('d8 hires >= 10')
def _(days): return days[8]['hires'] >= 10


@rule('d9 hires >= 10')
def _(days): return days[9]['hires'] >= 10


@rule('d10 hires >= 11')
def _(days): return days[10]['hires'] >= 11


@rule('max hires d0-16 <= 12')
def _(days): return max(days[d]['hires'] for d in range(17)) <= 12


@rule('d1 hires < d0 hires (skip-day)')
def _(days): return days[1]['hires'] < days[0]['hires']


@rule('d7 hires < min(d6, d8) (skip-day)')
def _(days): return days[7]['hires'] < min(days[6]['hires'], days[8]['hires'])


@rule('d1 wheat watered <= 20% of wheat tiles')
def _(days):
    r = days[1]; t = (r['crops'] or {}).get('WHEAT', 0)
    w = sum(v for k, v in (r['ops'] or {}).items() if k.startswith('WATER:WHEAT'))
    return t > 0 and w <= 0.2 * t


@rule('NE day hires >= day-before + 3')
def _(days):
    d, e = landday(days, 'NE')
    return d is not None and d >= 1 and days[d]['hires'] >= days[d - 1]['hires'] + 3


@rule('NE day: >= 15 plantings in NE same day')
def _(days):
    d, e = landday(days, 'NE')
    return d is not None and sum(v for k, v in (days[d]['ops'] or {}).items() if k.startswith('PLANT') and k.endswith('@NE')) >= 15


@rule('SW by day 9')
def _(days):
    d, e = landday(days, 'SW'); return d is not None and d <= 9


@rule('SW day hires >= 10, all hired before the land (h <= land hour)')
def _(days):
    d, e = landday(days, 'SW')
    return d is not None and days[d]['hires'] >= 10 and all(h <= e['h'] for h in days[d]['hire_h'])


@rule('SW day: >= 10 plantings in SW same day')
def _(days):
    d, e = landday(days, 'SW')
    return d is not None and sum(v for k, v in (days[d]['ops'] or {}).items() if k.startswith('PLANT') and k.endswith('@SW')) >= 10


@rule('d6-10: >= 8 hires at hour 0 on 3+ of 5 days')
def _(days): return sum(sum(h == 0 for h in days[d]['hire_h']) >= 8 for d in range(6, 11)) >= 3


@rule('d3-9: hour-0 hires cost > m0 on 3+ days (wage funded by same-hour sells)')
def _(days): return sum(fib_sum(sum(h == 0 for h in days[d]['hire_h'])) > (days[d]['m0'] or 0) for d in range(3, 10)) >= 3


@rule('d8-10 eff per unit in [9.5, 13]')
def _(days): return all(9.5 <= labour(days[d])['eff'] / (1 + days[d]['hires']) <= 13 for d in (8, 9, 10))


@rule('d0-5 idle (pass/noop) < 10% of unit-turns')
def _(days):
    L = [labour(days[d]) for d in range(6)]
    return sum(x['idle'] for x in L) < 0.1 * sum(x['ut'] for x in L)


@rule('hires d0-9 total >= 62')
def _(days): return sum(days[d]['hires'] for d in range(10)) >= 62


@rule('crew fit d6-16: |hires - (round(eff/11.5) - 1)| <= 1 on 80% of days')
def _(days):
    ok = sum(abs(days[d]['hires'] - (round(labour(days[d])['eff'] / 11.5) - 1)) <= 1 for d in range(6, 17))
    return ok >= 0.8 * 11


print('%-72s' % 'rule (% of seats)' + ''.join('%7s' % t for t in teams))
for name, fn in RULES.items():
    line = '%-72s' % name
    for t in teams:
        n = k = 0
        for key, days in S.items():
            if 0 not in days or team_of(days[0]) != t or not all(d in days for d in range(17)): continue
            n += 1; k += bool(fn(days))
        line += ' %5.0f%%' % (100 * k / max(1, n))
    print(line)
print('seats:', {t: sum(1 for days in S.values() if 0 in days and team_of(days[0]) == t) for t in teams})
