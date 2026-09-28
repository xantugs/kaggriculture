"""Wage counterfactuals for roster leveling: same hand-days, (a) fully flat over days A-B, (b) pull-forward only:
a hand may move from day d to day d-1 (harvest a day early), greedily while it lowers the Fibonacci wage bill,
at most K hands moved out of any one day. usage: level_cf.py daylog.jsonl [A B K]"""
import sys, json, statistics as st
fib = [1, 1]
while len(fib) < 40: fib.append(fib[-1] + fib[-2])
wage = lambda n: sum(fib[:max(0, n)])
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
A, B, K = (int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (20, 27, 2)
for who in ('us', 'elite'):
    paid = []; flat = []; pull = []
    for x in rows:
        h = [int(x['days_' + who][d]['mkt'].get('hires', 0)) for d in range(A, B + 1)]
        base = sum(wage(v) for v in h)
        tot = sum(h); n = len(h); lo = tot // n; k = tot - lo * n
        flat.append(base - (k * wage(lo + 1) + (n - k) * wage(lo)))
        g = list(h); moved = [0] * n
        while True:
            best = None
            for i in range(1, n):
                if moved[i] >= K: continue
                gain = (wage(g[i]) - wage(g[i] - 1)) - (wage(g[i - 1] + 1) - wage(g[i - 1]))
                if gain > 0 and (best is None or gain > best[0]): best = (gain, i)
            if best is None: break
            i = best[1]; g[i] -= 1; g[i - 1] += 1; moved[i] += 1
        pull.append(base - sum(wage(v) for v in g)); paid.append(base)
    print(f"{who:5s} days {A}-{B}: wage (from hire counts) {st.mean(paid):6.0f}  flat saves {st.mean(flat):5.0f}  pull-forward (<= {K} hands/day, one day) saves {st.mean(pull):5.0f}")
