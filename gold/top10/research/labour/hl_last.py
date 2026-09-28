"""What the last hired hand buys, per day (all crews): wage step, overflow units removed, musts, visit value by tag.
usage: hl_last.py rows.jsonl [d0 d1]"""
import sys, json, collections
FIB = [1, 1]
while len(FIB) < 30: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
d0 = int(sys.argv[2]) if len(sys.argv) > 2 else 16; d1 = int(sys.argv[3]) if len(sys.argv) > 3 else 28
per = collections.defaultdict(collections.Counter)
for r in rows:
    for d in r['hirelog']:
        if d['final'] or not d['trace'] or not (d0 <= d['day'] <= d1): continue
        tr = {t[0]: t for t in d['trace']}; ch = d['chosen']
        if ch - 1 not in tr or ch not in tr: continue
        tp, tc = tr[ch - 1], tr[ch]
        a = per[d['day']]; a['n'] += 1
        a['wage'] += CUM[ch] - CUM[ch - 1]
        a['ovf'] += tp[5] - tc[5]
        a['must'] += tp[4] > tc[4]
        vis = sum(v[1] for v in tp[6].values()) - sum(v[1] for v in tc[6].values())
        a['vis'] += vis
        a['ovfdriven'] += (tp[5] - tc[5]) * 100 > vis and tp[4] == tc[4]
print(f"{'day':>3} {'n':>4} {'last$':>6} {'ovf-u':>6} {'vis$':>7} {'must%':>6} {'ovf-driven%':>11}")
for day in sorted(per):
    a = per[day]; k = a['n']
    print(f"{day:3d} {k:4d} {a['wage']/k:6.0f} {a['ovf']/k:6.1f} {a['vis']/k:7.0f} {100*a['must']/k:6.0f} {100*a['ovfdriven']/k:11.0f}")
