"""What pays for SW: on the day of the SW purchase, sells by product in hours <= the SW hour (and animal buys before it),
plus hour-0 cash. Per team (23-26 Sep recorded) and T7."""
import json, os, collections
from lib import HERE, SHORT, med, mean
OM = os.path.dirname(HERE)
acc = collections.defaultdict(list)
for fn, role in (('elite_days.jsonl', 'rec'), ('ours_T7_days.jsonl', 'ours')):
    with open(os.path.join(OM, fn), encoding='utf-8') as f:
        for l in f:
            r = json.loads(l)
            if role == 'rec' and r['date'] < '2026-09-23':
                continue
            sw = [x for x in r['land'] if x['q'] == 'SW']
            if not sw or not r['detail']:
                continue
            h = sw[0]['h']
            t = SHORT[r['team']] if role == 'rec' else 'T7'
            s = collections.Counter()
            ba = 0
            for hh, op, item, n, usd in r['fills']:
                if hh <= h and op == 'S':
                    s[item] += usd
                if hh <= h and op == 'BA':
                    ba += usd
            acc[t].append(dict(d=r['d'], h=h, m0=r['m0'], cb=sw[0]['cash_before'], ba=ba, **{'s_' + k: v for k, v in s.items()}))
for t in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    E = acc[t]
    days = collections.Counter(e['d'] for e in E)
    print('%-5s n=%d SW day %s | hour med %.0f | m0 %.0f | sells up to SW hour: %s | animals bought before %.0f | cash before %.0f' % (
        t, len(E), dict(days.most_common(3)), med(e['h'] for e in E), mean(e['m0'] for e in E),
        ' '.join('%s %.0f' % (k[2:6], mean(e.get(k, 0) for e in E)) for k in ('s_MILK', 's_FERTILIZER', 's_WHEAT', 's_WOOL', 's_EGG', 's_STRAWBERRY', 's_MELON', 's_CARROT')),
        mean(e['ba'] for e in E), mean(e['cb'] for e in E)))
