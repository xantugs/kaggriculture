"""Counterfactual crews from logged hire-search traces: re-score each logged h with other overflow prices / caps.
usage: hl_cf.py rows.jsonl [d0 d1]"""
import sys, json, collections
FIB = [1, 1]
while len(FIB) < 30: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
d0 = int(sys.argv[2]) if len(sys.argv) > 2 else 16; d1 = int(sys.argv[3]) if len(sys.argv) > 3 else 28
n = len(rows)
def pick(trace, V, cap=99, w=0.6):
    best = None
    for t in trace:
        h, cost, pen, nun, nm, ovf = t[:6]
        if h > cap: continue
        p = pen - ovf * 100.0 + ovf * V
        s = -p - w * cost
        if best is None or s > best[0]:
            best = (s, h, cost, ovf, nm, p)
    return best
res = collections.defaultdict(collections.Counter)
for r in rows:
    for d in r['hirelog']:
        if d['final'] or not d['trace'] or not (d0 <= d['day'] <= d1): continue
        tr = d['trace']
        base = pick(tr, 100.0)
        for lab, V, cap in (('T5', 100, 99), ('ovf50', 50, 99), ('ovf30', 30, 99), ('ovf10', 10, 99), ('ovf0', 0, 99), ('cap13', 100, 13), ('cap12', 100, 12)):
            b = pick(tr, V, cap)
            a = res[lab]; a['h'] += b[1]; a['wage'] += b[2]; a['ovf'] += b[3]; a['must'] += b[4] > 0
            a['vis'] += (b[5] - b[3] * V) - (base[5] - base[3] * 100.0)   # non-overflow penalty added (unserved visit value)
            a['big'] += b[1] >= 13; a['days'] += 1
print(n, 'seats, days', d0, '-', d1, '(non-final controller days, as logged; hire weight 0.6)')
b = res['T5']
for lab, a in res.items():
    print(f"{lab:6s} crew {a['h']/a['days']:5.2f}  >=13 {a['big']/n:4.2f}/seat  wage ${a['wage']/n:5.0f}/seat (d ${(a['wage']-b['wage'])/n:+5.0f})"
          f"  overflow {a['ovf']/n:5.1f} u/seat (d {(a['ovf']-b['ovf'])/n:+5.1f})  unserved visit value d ${a['vis']/n:+5.0f}  must-left days {a['must']}")
