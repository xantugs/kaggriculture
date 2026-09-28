"""Per-day net cash-flow gap us - elite (mean per seat, +- SE) with the main line items, days d0..29.
usage: perday_gap.py rows.jsonl d0"""
import sys, json, math, statistics as st, collections
p, d0 = sys.argv[1], int(sys.argv[2])
rows = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
n = len(rows)
def net(f):
    s = 0.0; c = collections.Counter()
    for k, v in f.items():
        if k.startswith('S$'): s += v; c[k[2:]] += v
        elif k.startswith(('B$', 'seed$', 'anim$')) or k in ('land$', 'hire$'):
            s -= v
            kk = 'hire' if k == 'hire$' else ('buy' + k[2:5] if k.startswith('B$') else k[:4])
            c[kk] -= v
    return s, c
print(p.split('/')[-1], n)
cum = [0.0] * n
for D in range(d0, 30):
    g = []; items = collections.Counter()
    for i, x in enumerate(rows):
        su, cu = net(x['days_us'][D]['f']); se, ce = net(x['days_elite'][D]['f'])
        g.append(su - se); cum[i] += su - se
        for k in set(cu) | set(ce): items[k] += (cu[k] - ce[k]) / n
    top = ' '.join('%s %+.0f' % (k[:5], v) for k, v in sorted(items.items(), key=lambda kv: -abs(kv[1]))[:6])
    print('d%2d %+6.0f +-%4.0f  cum %+6.0f | %s' % (D, st.mean(g), st.pstdev(g) / math.sqrt(n), st.mean(cum), top))
print('final margin mean %+.0f' % st.mean(x['m'] for x in rows))
