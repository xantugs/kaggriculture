"""Wave amplitude of one-time-crop work (plantings + harvests of wheat/carrots) per day, us vs elite (probe rows).
usage: waves.py rows.jsonl[,more] [d0 d1]"""
import sys, json, statistics as st, collections
rows = [json.loads(l) for p in sys.argv[1].split(',') for l in open(p, encoding='utf-8')]
d0 = int(sys.argv[2]) if len(sys.argv) > 2 else 16; d1 = int(sys.argv[3]) if len(sys.argv) > 3 else 27
FIB = [1, 1]
while len(FIB) < 30: FIB.append(FIB[-1] + FIB[-2])
CUM = [sum(FIB[:n]) for n in range(30)]
def ser(days, keys):
    return [sum(days.get(str(d), {}).get(k, 0) for k in keys) for d in range(d0, d1 + 1)]
K_ONE = ['k:HARV:WHEAT', 'k:HARV:CARROT', 'k:PLAN:WHEAT', 'k:PLAN:CARROT']
agg = collections.defaultdict(list)
for r in rows:
    for side in ('days_us', 'days_elite'):
        s1 = ser(r[side], K_ONE); hs = ser(r[side], ['hire'])
        agg[side + 'mean'].append(st.mean(s1)); agg[side + 'sd'].append(st.pstdev(s1))
        agg[side + 'cv'].append(st.pstdev(s1) / max(1e-9, st.mean(s1)))
        agg[side + 'hsd'].append(st.pstdev(hs)); agg[side + 'hmean'].append(st.mean(hs))
        # correlation of daily one-time work with daily hands
        if st.pstdev(s1) > 0 and st.pstdev(hs) > 0:
            agg[side + 'corr'].append(st.correlation(s1, hs))
        w = sum(CUM[h] for h in hs); tot = sum(hs); n = len(hs); lo = tot // n; k = tot - lo * n
        agg[side + 'waste'].append(w - (k * CUM[lo + 1] + (n - k) * CUM[lo]))
for side in ('days_us', 'days_elite'):
    print(f"{side:11s} one-time work/day {st.mean(agg[side+'mean']):5.1f} sd {st.mean(agg[side+'sd']):5.1f} cv {st.mean(agg[side+'cv']):.2f}"
          f" | hands/day {st.mean(agg[side+'hmean']):5.2f} sd {st.mean(agg[side+'hsd']):.2f} | corr(work,hands) {(st.mean(agg[side+'corr']) if agg[side+'corr'] else float('nan')):+.2f}"
          f" | wage above flat roster ${st.mean(agg[side+'waste']):.0f}")
