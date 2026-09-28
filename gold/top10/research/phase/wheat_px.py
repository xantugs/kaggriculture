"""Realized wheat / fertilizer sell and buy prices by window, us vs elite, from gapday rows.
usage: wheat_px.py rows.jsonl [...]"""
import sys, json, collections
WIN = [(0, 6), (6, 12), (12, 16), (16, 22), (22, 26), (26, 30)]
for p in sys.argv[1:]:
    rows = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    print('==', p.split('/')[-1], len(rows))
    for prod in ('WHEAT', 'FERTILIZER', 'EGG', 'STRAWBERRY', 'MILK', 'WOOL', 'TOMATO', 'CARROT', 'MELON'):
        line = '%-10s' % prod[:10]
        for w in WIN:
            c = {s: collections.Counter() for s in ('days_us', 'days_elite')}
            for x in rows:
                for s in c:
                    for D in range(*w):
                        f = x[s][D]['f']
                        for k in ('S$', 'Su', 'B$', 'Bu'):
                            c[s][k] += f.get(k + prod, 0)
            u, e = c['days_us'], c['days_elite']
            px = lambda cc, a, b: cc[a] / cc[b] if cc[b] else float('nan')
            n = len(rows)
            line += ' | d%d-%d s %4.0f@%3.0f/%4.0f@%3.0f' % (w[0], w[1] - 1, u['Su'] / n, px(u, 'S$', 'Su'), e['Su'] / n, px(e, 'S$', 'Su'))
            if prod in ('WHEAT', 'FERTILIZER'):
                line += ' b %3.0f@%3.0f/%3.0f@%3.0f' % (u['Bu'] / n, px(u, 'B$', 'Bu'), e['Bu'] / n, px(e, 'B$', 'Bu'))
        print(line)
