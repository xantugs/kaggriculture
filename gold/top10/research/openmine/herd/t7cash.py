"""T7: could SW be bought earlier from the herd cash? Per seat: hour-0 cash, end-of-day cash and the max observed cash on
days 7-10; share of seats whose end-of-day cash >= $2,000 (SW affordable after all the day's tape purchases)."""
import json, os, collections
from lib import HERE, mean, med, pct
OM = os.path.dirname(HERE)
SIGN = {'S': 1, 'BP': -1, 'BS': -1, 'BA': -1, 'H': -1, 'L': -1}
by = collections.defaultdict(list)
with open(os.path.join(OM, 'ours_T7_days.jsonl'), encoding='utf-8') as f:
    for l in f:
        r = json.loads(l)
        if not 7 <= r['d'] <= 10:
            continue
        c = r['m0']; mx = c
        per = collections.defaultdict(float)
        for h, op, item, n, usd in r['fills']:
            per[h] += SIGN[op] * usd
        for h in range(24):
            c += per.get(h, 0)
            mx = max(mx, c)
        milk = (r['sell'].get('MILK') or [0, 0])[1]
        by[r['d']].append((r['m0'], r['mend'], mx, milk))
for d in sorted(by):
    v = by[d]
    print('d%d m0 med %5.0f | mend med %5.0f, >= $2000 in %3.0f%% | max in-day cash med %5.0f, >= $2000 in %3.0f%% | milk sold $%.0f' % (
        d, med(x[0] for x in v), med(x[1] for x in v), pct(x[1] >= 2000 for x in v), med(x[2] for x in v), pct(x[2] >= 2000 for x in v), mean(x[3] for x in v)))
