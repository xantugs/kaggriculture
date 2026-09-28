"""Flat-roster excess of the logged crews and of counterfactual crews (overflow price V), days d0-d1.
usage: hl_flat.py rows.jsonl [d0 d1]"""
import sys, json, statistics as st
FIB = [1, 1]
while len(FIB) < 30: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
d0 = int(sys.argv[2]) if len(sys.argv) > 2 else 16; d1 = int(sys.argv[3]) if len(sys.argv) > 3 else 28
def pick(trace, V):
    best = None
    for t in trace:
        h, cost, pen, nun, nm, ovf = t[:6]
        s = -(pen - ovf * 100.0 + ovf * V) - 0.6 * cost
        if best is None or s > best[0]:
            best = (s, h)
    return best[1]
def excess(hs):
    tot = sum(hs); m = len(hs); lo = tot // m; k = tot - lo * m
    return sum(CUM[h] for h in hs) - (k * CUM[lo + 1] + (m - k) * CUM[lo])
for V in (100, 30, 0):
    ex = []; sd = []; mean = []
    for r in rows:
        hl = {d['day']: d for d in r['hirelog'] if not d['final'] and d['trace']}
        hs = [pick(hl[d]['trace'], V) if d in hl else r['days_us'].get(str(d), {}).get('hire', 0) for d in range(d0, d1 + 1)]
        ex.append(excess(hs)); sd.append(st.pstdev(hs)); mean.append(st.mean(hs))
    print(f"overflow ${V:3d}/unit: crew {st.mean(mean):5.2f} sd {st.mean(sd):.2f}  wage above a flat roster ${st.mean(ex):4.0f}/seat")
ex = [excess([r['days_elite'].get(str(d), {}).get('hire', 0) for d in range(d0, d1 + 1)]) for r in rows]
print(f"elite (actual): wage above a flat roster ${st.mean(ex):4.0f}/seat")
