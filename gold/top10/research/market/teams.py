"""Per team: net product revenue gap (sales - purchases, us - elite) and its volume / price split, plus win rate.
usage: teams.py rows.jsonl[,more]"""
import sys, collections
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')
from ana_fills import P, load

rows = list(load(sys.argv[1]))
by = collections.defaultdict(list)
for r in rows:
    by[r['team']].append(r)
by['ALL'] = rows
print("team                  n  win%   margin | net revenue gap per product (us - elite), [vol/price] for sales")
for team, rs in sorted(by.items(), key=lambda kv: (kv[0] == 'ALL', kv[0])):
    n = len(rs)
    U = collections.defaultdict(float); R = collections.defaultdict(float); B = collections.defaultdict(float)
    for r in rs:
        for t, sd, op, it, k, d in r['fills']:
            if op == 'S': U[(sd, it)] += k; R[(sd, it)] += d
            else: B[(sd, it)] += d
    parts = []
    for it in P:
        uu, ue = U[(0, it)] / n, U[(1, it)] / n; ru, re_ = R[(0, it)] / n, R[(1, it)] / n
        net = (ru - B[(0, it)] / n) - (re_ - B[(1, it)] / n)
        pbar = (ru + re_) / (uu + ue) if uu + ue else 0
        vol = (uu - ue) * pbar
        parts.append(f"{it[:4]} {net:+6.0f}[{vol:+6.0f}/{ru - re_ - vol:+5.0f}]")
    print(f"{team[:20]:20s} {n:3d} {100*sum(r['m'] > 0 for r in rs)/n:4.0f}% {sum(r['m'] for r in rs)/n:+7.0f} | " + " ".join(parts))
