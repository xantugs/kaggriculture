"""Hybrid ladder: controller-from-day-D margins vs the elite's own continuation, paired per seat, with SEs.
usage: ladder.py gate [prefix] [base suffix: sf8 or T5]   prefix: gapday_hyb (sf8 controller, default) or gapday_T5hyb
Prints for the seats present in every file: m(sf8 full game), m(D) for D in 12,16,22,30, the per-window elite edge
m(D2) - m(D1) (what the elite's own play in [D1, D2) is worth over our controller's on the same farm) and the
controller-valued state gap at D = m(sf8) - m(D), all +- SE, plus wins."""
import sys, os, json, math, statistics as st
H = os.path.dirname(os.path.abspath(__file__))
g = sys.argv[1]; pre = sys.argv[2] if len(sys.argv) > 2 else 'gapday_hyb'; bsuf = sys.argv[3] if len(sys.argv) > 3 else 'sf8'


def rows(p):
    if not os.path.exists(p): return None
    return {(x['gid'], x['seat']): x['m'] for x in map(json.loads, (l for l in open(p, encoding='utf-8') if l.strip())) if x['m'] is not None}


base = rows(os.path.join(H, 'gapday_%s_%s.jsonl' % (g, bsuf)))
hy = {D: rows(os.path.join(H, '%s%d_%s.jsonl' % (pre, D, g))) for D in (12, 16, 22, 30)}
hy = {D: v for D, v in hy.items() if v}
Ds = sorted(d for d in hy if d < 30)
ks = [k for k in base if all(k in hy[D] for D in Ds)]
n = len(ks)
se = lambda v: st.pstdev(v) / math.sqrt(len(v))
print('%s %s: %d seats in every file (D %s)' % (g, pre, n, Ds))
mb = [base[k] for k in ks]
print('  sf8 full game     m %+6.0f +-%4.0f  wins %d' % (st.mean(mb), se(mb), sum(m > 0 for m in mb)))
for D in Ds:
    v = [hy[D][k] for k in ks]; gap = [base[k] - hy[D][k] for k in ks]
    print('  controller from %2d m %+6.0f +-%4.0f  wins %2d | state gap at D (sf8 - hyb) %+6.0f +-%4.0f' % (
        D, st.mean(v), se(v), sum(m > 0 for m in v), st.mean(gap), se(gap)))
for a, b in zip(Ds, Ds[1:] + [30]):
    if b == 30:
        v = [-hy[a][k] for k in ks]
        print('  elite edge days %2d-29 (0 - m(%d))       %+6.0f +-%4.0f  (%.0f/day)' % (a, a, st.mean(v), se(v), st.mean(v) / (30 - a)))
    else:
        v = [hy[b][k] - hy[a][k] for k in ks]
        print('  elite edge days %2d-%2d (m(%d) - m(%d))  %+6.0f +-%4.0f  (%.0f/day)' % (a, b - 1, b, a, st.mean(v), se(v), st.mean(v) / (b - a)))
if 30 in hy:
    v = list(hy[30].values())
    print('  mirror noise (D=30, %d seats): %+.0f +- %.0f' % (len(v), st.mean(v), se(v)))
