"""Per product and day: mean book quote at hour 1 and hour 21, units sold and $/unit by each side (per seat).
usage: daily.py rows.jsonl PRODUCT [team_filter]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P, price, load
rows = list(load(sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else None)); it = sys.argv[2]; pi = P.index(it); n = len(rows)
U = collections.defaultdict(float); R = collections.defaultdict(float); Q = collections.defaultdict(float)
for r in rows:
    for d in range(30):
        for h in (1, 21):
            t = d * 24 + h
            if t - 1 < len(r['inv']): Q[(d, h)] += price(it, r['inv'][t - 1][pi])
    for t, sd, op, p, k, dl in r['fills']:
        if p == it and op == 'S': U[(t // 24, sd)] += k; R[(t // 24, sd)] += dl
print(f"{it}, {n} seats: day, quote h1, quote h21, units us, $/u us, units el, $/u el")
for d in range(30):
    uu, ue = U[(d, 0)] / n, U[(d, 1)] / n
    if uu + ue < 0.05: continue
    print(f"  d{d:2d} q1 {Q[(d,1)]/n:6.1f} q21 {Q[(d,21)]/n:6.1f}  us {uu:5.1f} @ {R[(d,0)]/max(1e-9,U[(d,0)]):6.1f}   el {ue:5.1f} @ {R[(d,1)]/max(1e-9,U[(d,1)]):6.1f}")
