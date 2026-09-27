"""Roster shape: hires per day and wage bill, us vs elite, days 16-28; how much a flat roster with the same hand-days would save."""
import sys, json, statistics as st
fib = [1, 1]
while len(fib) < 30: fib.append(fib[-1] + fib[-2])
wage = lambda n: sum(fib[:n])
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p, encoding='utf-8')]
rows = [x for x in rows if x['m'] is not None and len(x['days_us']) >= 29]
oth = 'elite' if 'days_elite' in rows[0] else 'them'
for name, sel in (('ALL', rows), ('L<5k', [x for x in rows if -5000 < x['m'] < 0]), ('W<5k', [x for x in rows if 0 < x['m'] < 5000]), ('L>5k', [x for x in rows if x['m'] <= -5000])):
    if not sel: continue
    out = []
    for who in ('us', oth):
        hd = []; paid = []; flat = []; sd = []
        for x in sel:
            h = [x['days_' + who][d]['mkt'].get('hires', 0) for d in range(16, 29)]
            c = [x['days_' + who][d]['mkt'].get('hire$', 0) for d in range(16, 29)]
            tot = sum(h); n = len(h)
            lo = tot // n; k = tot - lo * n   # flat: k days at lo+1, the rest at lo
            flat.append(k * wage(lo + 1) + (n - k) * wage(lo)); paid.append(sum(c)); hd.append(tot); sd.append(st.pstdev(h))
        out.append((who, st.mean(hd), st.mean(paid), st.mean(flat), st.mean(sd)))
    print(f"{name:5s} n={len(sel):3d} " + ' | '.join(f"{w}: hand-days {a:5.1f} paid ${b:5.0f} flat ${c:5.0f} (excess ${b-c:4.0f}) sd/day {s:.2f}" for w, a, b, c, s in out))
