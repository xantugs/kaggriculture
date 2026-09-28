"""Animal purchases by day and kind (mean units per seat), herd at hour 0, idle cash, fertilizer engine.
Recorded elite 23-26 Sep next to T7 (96 seats in the same towns) and the recorded elite of those same 96 games."""
import collections, statistics as st
from common import load, by_team, SHORT, TEAMS, pairs

S = load()
groups = by_team(S, 'rec')
P = pairs(S)
groups['T7'] = [p[0] for p in P]
order = TEAMS + ['T7']
D = 13


def m(xs):
    return sum(xs) / len(xs) if xs else float('nan')


print('== animals bought per day (mean units/seat): C=cow S=sheep G=goose')
print('%-5s ' % 'team' + ''.join('%11s' % ('d%d' % d) for d in range(D)))
for t in order:
    ss = groups[t]
    cells = []
    for d in range(D):
        c = collections.Counter()
        for s in ss:
            for k, (n, v) in (s['days'][d].get('buy_animal') or {}).items():
                c[k] += n
        cells.append('%3.1f/%3.1f/%3.1f' % (c['COW'] / len(ss), c['SHEEP'] / len(ss), c['GOOSE'] / len(ss)))
    print('%-5s ' % SHORT[t] + ''.join('%11s' % x for x in cells))

print('\n== owned animals at hour 0 (placed + in shed), total C+S+G, and cum animal-days thru d8')
print('%-5s ' % 'team' + ''.join('%6s' % ('d%d' % d) for d in range(D)) + '  anim-days0-8  geese d10  cows d10 sheep d10')
for t in order:
    ss = groups[t]
    tot = []
    for d in range(D):
        v = []
        for s in ss:
            r = s['days'][d]
            h = sum((r.get('herd') or {}).values())
            sh = r.get('shed') or {}
            h += sum(sh.get(k, 0) for k in ('COW', 'SHEEP', 'GOOSE'))
            v.append(h)
        tot.append(m(v))
    ad = sum(tot[:9])
    g10 = m([(s['days'][10].get('herd') or {}).get('GOOSE', 0) for s in ss])
    c10 = m([(s['days'][10].get('herd') or {}).get('COW', 0) for s in ss])
    s10 = m([(s['days'][10].get('herd') or {}).get('SHEEP', 0) for s in ss])
    print('%-5s ' % SHORT[t] + ''.join('%6.1f' % x for x in tot) + '  %8.1f     %5.1f     %5.1f    %5.1f' % (ad, g10, c10, s10))

print('\n== day-0 purchases: cows / sheep / geese distribution (share of seats)')
for t in order:
    ss = groups[t]
    c = collections.Counter()
    for s in ss:
        ba = s['days'][0].get('buy_animal') or {}
        c[(ba.get('COW', [0])[0], ba.get('SHEEP', [0])[0], ba.get('GOOSE', [0])[0])] += 1
    print('  %-5s' % SHORT[t], ', '.join('%dC%dS%dG %2.0f%%' % (k[0], k[1], k[2], 100 * v / len(ss)) for k, v in c.most_common(4)))

print('\n== idle cash: mean hour-0 cash, and share of seat-days d1-d9 starting with < $150')
for t in order:
    ss = groups[t]
    m0 = [s['days'][d]['m0'] for s in ss for d in range(1, 10)]
    print('  %-5s mean m0 d1-9 %6.0f   share<150 %3.0f%%   share>=500 %3.0f%%   by day: %s' % (
        SHORT[t], m(m0), 100 * sum(x < 150 for x in m0) / len(m0), 100 * sum(x >= 500 for x in m0) / len(m0),
        ' '.join('%d' % m([s['days'][d]['m0'] for s in ss]) for d in range(1, 11))))

print('\n== fertilizer engine: collected (COLLECT_FERTILIZER), sold units, bought units, avg sell price, FERTILIZE used, per day')
for t in order:
    ss = groups[t]
    row = []
    for d in range(D):
        col = sold = bought = used = 0; val = 0.0
        for s in ss:
            r = s['days'][d]
            ops = r.get('ops') or {}
            col += sum(v for k, v in ops.items() if k.startswith('COLLECT_FERTILIZER'))
            used += sum(v for k, v in ops.items() if k.startswith('FERTILIZE:'))
            x = (r.get('sell') or {}).get('FERTILIZER')
            if x:
                sold += x[0]; val += x[1]
            y = (r.get('buy_prod') or {}).get('FERTILIZER')
            if y:
                bought += y[0]
        n = len(ss)
        row.append('%4.1f/%4.1f/%3.1f/%3.1f@%3.0f' % (col / n, sold / n, bought / n, used / n, val / sold if sold else 0))
    print('  %-5s' % SHORT[t], ' '.join(row[:10]))
print('  (collected/sold/bought/used@price per day, d0..d9)')
