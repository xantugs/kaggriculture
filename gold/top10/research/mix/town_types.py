"""sf8 gate margin and per-product ledger gap (us - elite) by shop counts among the first k shops, plus an OLS of the margin
on the shop counts. usage: town_types.py [k]"""
import json, collections, sys
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
k = int(sys.argv[1]) if len(sys.argv) > 1 else 4
G = 'gold/top10/gates/'
rows = []
for g in ('goldg', 'top10g'):
    refs = {(r['gid'], r['seat']): r for r in map(json.loads, open(G + g + '_refs.jsonl', encoding='utf-8'))}
    for x in map(json.loads, open(G + g + '_sf8.jsonl', encoding='utf-8')):
        x['shops'] = refs[(x['gid'], x['seat'])]['shops']; rows.append(x)
PR = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'EGG', 'MILK', 'WOOL', 'MELON', 'FERTILIZER', 'hire', 'anim', 'seed']
SH = sorted(SHOPS)
print(f'{len(rows)} seats, shops among the first {k}')
print(f"{'shop':15s} {'cnt':>3} {'n':>4} {'win%':>5} {'margin':>7} | " + ' '.join(f'{p[:5]:>6s}' for p in PR))
for s in SH:
    for c in (0, 1, 2):
        R = [x for x in rows if (x['shops'][:k].count(s) == c if c < 2 else x['shops'][:k].count(s) >= 2)]
        if len(R) < 8: continue
        gap = {p: sum(x['led_us'].get(p, 0) - x['led_elite'].get(p, 0) for x in R) / len(R) for p in PR}
        print(f"{s:15s} {c:3d} {len(R):4d} {100*sum(x['m']>0 for x in R)/len(R):5.0f} {sum(x['m'] for x in R)/len(R):+7.0f} | " + ' '.join(f'{gap[p]:+6.0f}' for p in PR))
def ols(X, y):
    n, m = len(X), len(X[0])
    A = [[sum(X[r][i] * X[r][j] for r in range(n)) for j in range(m)] for i in range(m)]
    bb = [sum(X[r][i] * y[r] for r in range(n)) for i in range(m)]
    M = [A[i][:] + [bb[i]] + [1.0 if j == i else 0.0 for j in range(m)] for i in range(m)]
    for c in range(m):
        piv = max(range(c, m), key=lambda r: abs(M[r][c])); M[c], M[piv] = M[piv], M[c]
        pv = M[c][c]
        if abs(pv) < 1e-12: continue
        M[c] = [v / pv for v in M[c]]
        for r in range(m):
            if r != c and M[r][c]:
                f = M[r][c]; M[r] = [a - f * b_ for a, b_ in zip(M[r], M[c])]
    beta = [M[i][m] for i in range(m)]; inv = [M[i][m + 1:] for i in range(m)]
    res = [y[r] - sum(X[r][j] * beta[j] for j in range(m)) for r in range(n)]
    s2 = sum(e * e for e in res) / (n - m)
    return beta, [max(0, s2 * inv[i][i]) ** 0.5 for i in range(m)]
X = [[1.0] + [x['shops'][:k].count(s) for s in SH] for x in rows]; y = [x['m'] for x in rows]
b, se = ols(X, y)
print('OLS margin ~ shop counts:', ' '.join(f'{n}={v:+.0f}({e:.0f})' for n, v, e in zip(['const'] + SH, b, se)))
