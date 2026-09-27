"""Hire-search log analysis (rows from hirelog_run.py).
For every controller day: which hand count the search chose, what drove it (overflow units vs unserved visit value),
and what alternative pricings would choose (model-implied wage saved vs model penalty added).
usage: hl_ana.py rows.jsonl[,more]"""
import sys, json, collections
FIB = [1, 1]
while len(FIB) < 30: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
rows = [json.loads(l) for p in sys.argv[1].split(',') for l in open(p, encoding='utf-8')]
print(len(rows), 'seats')

SCHEMES = {
    'sf8 (0.6)': lambda h, c: 0.6 * c,
    'wt11': lambda h, c: 0.6 * c + 0.4 * max(0, c - CUM[11]),
    'wt10': lambda h, c: 0.6 * c + 0.4 * max(0, c - CUM[10]),
    'full 1.0': lambda h, c: 1.0 * c,
}
OVF = {'ovf100': 100.0, 'ovf30': 30.0}

def choose(trace, costf, ovf_v):
    best = None
    for (h, c, pen, nun, nmust, ovf) in trace:
        p = pen - ovf * 100.0 + ovf * ovf_v
        s = -p - costf(h, c)
        if best is None or s > best[0]:
            best = (s, h, c, pen, ovf, nmust)
    return best

agg = collections.defaultdict(lambda: collections.Counter())
dist = collections.Counter(); drivers = collections.Counter()
for r in rows:
    for d in r['hirelog']:
        if d['final'] or not d['trace']:
            continue
        tr = [tuple(t) for t in d['trace']]
        ch = d['chosen']
        dist[ch] += 1
        base = choose(tr, SCHEMES['sf8 (0.6)'], 100.0)
        if ch >= 13:
            t12 = next((t for t in tr if t[0] == 12), None)
            tc = next((t for t in tr if t[0] == ch), None)
            if t12 and tc:
                d_ovf = (t12[5] - tc[5]) * 100.0
                d_vis = (t12[2] - t12[5] * 100.0) - (tc[2] - tc[5] * 100.0)
                must12 = t12[4]
                drivers['days>=13'] += 1
                drivers['must_unserved_at_12'] += must12 > 0
                drivers['ovf_part$'] += d_ovf; drivers['visit_part$'] += d_vis
                drivers['wage_above_12$'] += CUM[ch] - CUM[12]
        for sname, sf in SCHEMES.items():
            for oname, ov in OVF.items():
                b = choose(tr, sf, ov)
                a = agg[(sname, oname)]
                a['days'] += 1; a['hands'] += b[1]; a['wage'] += b[2]
                a['pen_model'] += b[3]  # penalty at sf8's pricing of overflow (100/unit)
                a['ovf_units'] += b[4]; a['must_left'] += b[5] > 0
n = len(rows)
print('chosen hands on non-final controller days:', dict(sorted(dist.items())))
k = max(1, drivers['days>=13'])
print(f"days with >=13 hands: {drivers['days>=13']} ({drivers['days>=13']/n:.2f}/seat); musts unserved at 12 on {drivers['must_unserved_at_12']};"
      f" per such day: wage above 12 ${drivers['wage_above_12$']/k:.0f}, overflow penalty removed ${drivers['ovf_part$']/k:.0f},"
      f" visit value added ${drivers['visit_part$']/k:.0f}")
b0 = agg[('sf8 (0.6)', 'ovf100')]
print(f"{'scheme':12s} {'ovf':7s} {'hands/day':>9} {'wage/seat':>9} {'dWage':>7} {'dPen(model)':>11} {'ovf u/seat':>10} {'must-left days':>14}")
for (s, o), a in sorted(agg.items()):
    print(f"{s:12s} {o:7s} {a['hands']/a['days']:9.2f} {a['wage']/n:9.0f} {(a['wage']-b0['wage'])/n:+7.0f} {(a['pen_model']-b0['pen_model'])/n:+11.0f} {a['ovf_units']/n:10.1f} {a['must_left']:14d}")
