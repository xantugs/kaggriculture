"""Hire-search logs of a full-build research run (patch_hirelog_full.py + hirelog_run.py): what drives the peaks, how much
slack the troughs have, and which day pairs a levelled crew could merge.
usage: hl_t5.py rows.jsonl [d0 d1]"""
import sys, json, collections, statistics as st
FIB = [1, 1]
while len(FIB) < 30: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
d0 = int(sys.argv[2]) if len(sys.argv) > 2 else 16; d1 = int(sys.argv[3]) if len(sys.argv) > 3 else 28
n = len(rows)
print(n, 'seats; days', d0, '-', d1)

# 1. per-day: chosen crew, what is unserved at 12 / at chosen-1, overflow at 12, slack at the chosen crew
per = collections.defaultdict(lambda: collections.Counter())
drv = collections.Counter(); drv_tags = collections.Counter(); drv_val = collections.Counter()
for r in rows:
    for d in r['hirelog']:
        if d['final'] or not d['trace'] or not (d0 <= d['day'] <= d1):
            continue
        day = d['day']; ch = d['chosen']; tr = {t[0]: t for t in d['trace']}
        a = per[day]; a['n'] += 1; a['ch'] += ch; a['big'] += ch >= 13; a['wage'] += CUM[ch]
        use = [u for u in (d.get('use') or []) if u]
        slack = sum(max(0, c - rc) for rc, c in use[1:])          # hands only (unit 0 is the farmer)
        a['slack'] += slack; a['cap'] += sum(c for rc, c in use[1:])
        a['short'] += sum(1 for rc, c in use[1:] if rc <= c - 6)  # hands with >= 6 idle turns
        if 12 in tr:
            a['ovf12'] += tr[12][5]
        if ch >= 13 and (ch - 1) in tr:
            tp, tc = tr[ch - 1], tr[ch]
            drv['days'] += 1
            drv['ovf'] += (tp[5] - tc[5])
            drv['must'] += tp[4] > 0
            drv['wage_step'] += CUM[ch] - CUM[ch - 1]
            up, uc = tp[6], tc[6]
            for tag in set(up) | set(uc):
                nv = up.get(tag, [0, 0])[0] - uc.get(tag, [0, 0])[0]
                vv = up.get(tag, [0, 0])[1] - uc.get(tag, [0, 0])[1]
                drv_tags[tag] += nv; drv_val[tag] += vv
print(f"{'day':>3} {'crew':>5} {'>=13':>5} {'wage':>5} {'slack':>6} {'short':>5} {'ovf12':>5}")
for day in sorted(per):
    a = per[day]; k = a['n']
    print(f"{day:3d} {a['ch']/k:5.1f} {a['big']/k:5.2f} {a['wage']/k:5.0f} {a['slack']/k:6.1f} {a['short']/k:5.1f} {a['ovf12']/k:5.1f}")
k = max(1, drv['days'])
print(f"\nlast hand on crews >= 13: {drv['days']} days ({drv['days']/n:.2f}/seat); wage of that hand ${drv['wage_step']/k:.0f};"
      f" overflow units it removes {drv['ovf']/k:.1f}; a must left without it on {drv['must']} days")
print('  visits it serves (per such day): ' + ', '.join(f"{t} {drv_tags[t]/k:.1f} (${drv_val[t]/k:.0f})" for t in sorted(drv_tags, key=lambda t: -drv_val[t])))

# 2. crew profile and wage above a flat roster
waste = []; sdv = []; corr = []
for r in rows:
    hs = [r['days_us'].get(str(d), {}).get('hire', 0) for d in range(d0, d1 + 1)]
    wk = [sum(r['days_us'].get(str(d), {}).get(kk, 0) for kk in ('k:HARV:WHEAT', 'k:HARV:CARROT', 'k:PLAN:WHEAT', 'k:PLAN:CARROT'))
          for d in range(d0, d1 + 1)]
    tot = sum(hs); m = len(hs); lo = tot // m; kk = tot - lo * m
    waste.append(sum(CUM[h] for h in hs) - (kk * CUM[lo + 1] + (m - kk) * CUM[lo])); sdv.append(st.pstdev(hs))
    if st.pstdev(hs) > 0 and st.pstdev(wk) > 0:
        corr.append(st.correlation(hs, wk))
print(f"\ncrew sd {st.mean(sdv):.2f}; wage above a flat roster ${st.mean(waste):.0f}/seat; corr(one-time crop work, crew) {st.mean(corr):+.2f}")

# 3. adjacent day pairs a levelled crew could merge: (d, d+1) with crews differing by >= 3
pairs = collections.Counter()
for r in rows:
    hs = {int(dd): c.get('hire', 0) for dd, c in r['days_us'].items()}
    for d in range(d0, d1):
        a, b = hs.get(d, 0), hs.get(d + 1, 0)
        if abs(a - b) >= 3 and max(a, b) >= 12:
            lo = (a + b) // 2; hi = a + b - lo
            pairs['n'] += 1; pairs['save'] += CUM[a] + CUM[b] - CUM[lo] - CUM[hi]
            pairs['fwd' if b > a else 'back'] += 1
print(f"day pairs with a crew step >= 3 into a >= 12 crew: {pairs['n']/n:.2f}/seat, levelled saving ${pairs['save']/n:.0f}/seat"
      f" (peak after the trough {pairs['fwd']/n:.2f}, before {pairs['back']/n:.2f})")
