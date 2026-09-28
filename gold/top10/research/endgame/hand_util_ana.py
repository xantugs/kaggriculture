"""Summarise hand_util.py output: per day, hands, and per hire-rank the work/move/pass/idle turns (hands spawn at hour 1,
so a hand has 23 turns; idle = 23 - actions)."""
import sys, json, statistics as st, collections
rows = [json.loads(l) for p in sys.argv[1:] for l in open(p, encoding='utf-8')]
fib = [1, 1]
while len(fib) < 30: fib.append(fib[-1] + fib[-2])
print(len(rows), 'seats')
for d in range(16, 30):
    agg = collections.defaultdict(lambda: collections.Counter()); nh = []
    for x in rows:
        U = x['units'].get(str(d), {})
        n = x['nh'].get(str(d), 0); nh.append(n)
        for i in range(1, n + 1):
            c = U.get(str(i), {})
            w = sum(v for k, v in c.items() if k not in ('MOVE', 'PASS'))
            rank = i - n   # 0 = last hired, -1 = second last...
            key = 'last' if rank == 0 else ('last-1' if rank == -1 else ('last-2' if rank == -2 else 'others'))
            agg[key]['w'] += w; agg[key]['m'] += c.get('MOVE', 0); agg[key]['p'] += c.get('PASS', 0); agg[key]['n'] += 1
            agg[key]['idle'] += max(0, 23 - sum(c.values()))
    s = []
    for key in ('others', 'last-2', 'last-1', 'last'):
        a = agg[key]; k = max(1, a['n'])
        s.append(f"{key}: work {a['w']/k:4.1f} move {a['m']/k:4.1f} pass {a['p']/k:4.1f} idle {a['idle']/k:4.1f}")
    print(f"d{d} hands {st.mean(nh):4.1f} | " + ' | '.join(s))
