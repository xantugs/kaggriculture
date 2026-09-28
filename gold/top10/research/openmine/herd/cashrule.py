"""Cash rule of animal buys, days 1-9: at each hour with an animal fill, cash at the observation, same-hour sells, same-hour
other spend, and the cash left after the hour (reserve). Idle: share of hours 0-20 of days 2-9 whose observed cash >= $300
(a goose) with no animal bought that hour or later that day; mean observed cash over hours 0-23 of days 2-9."""
import json, os, collections
from lib import HERE, SHORT, med, mean
OM = os.path.dirname(HERE)
SIGN = {'S': 1, 'BP': -1, 'BS': -1, 'BA': -1, 'H': -1, 'L': -1}
ev = collections.defaultdict(list)
idle = collections.defaultdict(list)
avgc = collections.defaultdict(list)
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    with open(os.path.join(OM, fn), encoding='utf-8') as f:
        for l in f:
            r = json.loads(l)
            d = r['d']
            if d < 1 or d > 9 or (role == 'rec' and r['date'] < '2026-09-23'):
                continue
            t = SHORT[r['team']] if role == 'rec' else 'T7'
            per = collections.defaultdict(lambda: collections.Counter())
            for h, op, item, n, usd in r['fills']:
                per[h][op] += usd
                if op == 'BA':
                    per[h]['BA:' + item] += n
            c = r['m0']
            cash_obs = []
            for h in range(24):
                cash_obs.append(c)
                p = per.get(h, {})
                c += sum(SIGN[k] * v for k, v in p.items() if k in SIGN)
            last_ba = max([h for h in per if per[h].get('BA')] or [-1])
            for h in sorted(per):
                p = per[h]
                if p.get('BA'):
                    kinds = '+'.join(k[3] for k in p if k.startswith('BA:'))
                    after = cash_obs[h] + sum(SIGN[k] * v for k, v in p.items() if k in SIGN)
                    ev[(t, d)].append((cash_obs[h], p.get('S', 0), p.get('BS', 0) + p.get('BP', 0) + p.get('H', 0) + p.get('L', 0), p['BA'], after, kinds))
            if d >= 2:
                idle[t].append(sum(1 for h in range(21) if cash_obs[h] >= 300 and h > last_ba) / 21.0)
                avgc[t].append(mean(cash_obs))
for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    print('=====', t, ' mean observed cash d2-9 %.0f, share of hours 0-20 idle with >= $300 and no later animal buy that day %.0f%%' % (mean(avgc[t]), 100 * mean(idle[t])))
    for d in range(1, 10):
        E = ev[(t, d)]
        if not E:
            continue
        print('  d%d n=%4d cash_obs med %5.0f | same-hour sells med %5.0f (share>0 %3.0f%%) | other spend med %4.0f | animal $ med %4.0f | after med %4.0f p90 %4.0f' % (
            d, len(E), med(e[0] for e in E), med(e[1] for e in E), 100 * mean(e[1] > 0 for e in E), med(e[2] for e in E), med(e[3] for e in E),
            med(e[4] for e in E), sorted(e[4] for e in E)[int(0.9 * len(E))]))
