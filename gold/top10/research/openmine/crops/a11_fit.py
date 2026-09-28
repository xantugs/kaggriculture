"""What sets the NE / SW strawberry counts: least squares on shops known, rival strawberry tiles, cash.
usage: a11_fit.py"""
import sys, os, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import a8_rules as A


def lstsq(X, Y):
    k = len(X[0])
    M = [[sum(x[i] * x[j] for x in X) for j in range(k)] + [sum(x[i] * y for x, y in zip(X, Y))] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-12:
            continue
        for r in range(k):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [a - f * b for a, b in zip(M[r], M[c])]
    b = [M[i][k] / M[i][i] if abs(M[i][i]) > 1e-12 else 0 for i in range(k)]
    pred = [sum(bi * xi for bi, xi in zip(b, x)) for x in X]
    my = st.mean(Y)
    ss = sum((y - my) ** 2 for y in Y)
    r2 = 1 - sum((y - p) ** 2 for y, p in zip(Y, pred)) / ss if ss else float('nan')
    return b, r2


print('NE strawberries (NE buy day and next) ~ const + straw buyers known + rival straw tiles (h0) + own cash/1000 (h0)')
for g in ['Boey', 'FQ', 'TFC', 'CBF', 'Yiz', 'T7']:
    X = []; Y = []
    for key, rows in A.seats[g]:
        ne = A.landday(rows, 'NE')
        if ne is None: continue
        X.append([1, A.nb(rows, ne, A.SB), (rows[ne]['riv_crops'] or {}).get('STRAWBERRY', 0), rows[ne]['m0'] / 1000])
        Y.append(A.pl(rows, 'STRAWBERRY', ne, min(16, ne + 1), 'NE'))
    b, r2 = lstsq(X, Y)
    print(f'  {g:5s} n={len(Y):3d} const {b[0]:5.1f} buyers {b[1]:+5.1f} rivStraw {b[2]:+5.2f} cash/k {b[3]:+5.2f}  R2 {r2:.2f}')
    for s in (0, 1, 2):
        ys = [y for x, y in zip(X, Y) if x[1] == s]
        if ys: print(f'        buyers={s}: mean {st.mean(ys):5.1f} sd {st.pstdev(ys):4.1f} n {len(ys)}')
print('\nSW strawberries (SW buy day..+3) ~ const + straw buyers known on SW buy day + NE strawberries')
for g in ['Boey', 'FQ', 'TFC', 'CBF', 'Yiz', 'T7']:
    X = []; Y = []
    for key, rows in A.seats[g]:
        sw = A.landday(rows, 'SW'); ne = A.landday(rows, 'NE')
        if sw is None or ne is None: continue
        X.append([1, A.nb(rows, sw, A.SB), A.pl(rows, 'STRAWBERRY', ne, min(16, ne + 1), 'NE')])
        Y.append(A.pl(rows, 'STRAWBERRY', sw, min(16, sw + 3), 'SW'))
    b, r2 = lstsq(X, Y)
    print(f'  {g:5s} n={len(Y):3d} const {b[0]:5.1f} buyers {b[1]:+5.1f} NEstraw {b[2]:+5.2f}  R2 {r2:.2f}')
print('\nNE wheat (buy day and next) ~ const + straw buyers + wheat buyers known')
WB = {'BAKERY', 'PIZZA_SHOP', 'BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'FARMERS_MARKET'}
for g in ['Boey', 'FQ', 'TFC', 'CBF', 'Yiz', 'T7']:
    X = []; Y = []
    for key, rows in A.seats[g]:
        ne = A.landday(rows, 'NE')
        if ne is None: continue
        X.append([1, A.nb(rows, ne, A.SB), A.nb(rows, ne, WB)])
        Y.append(A.pl(rows, 'WHEAT', ne, min(16, ne + 1), 'NE'))
    b, r2 = lstsq(X, Y)
    print(f'  {g:5s} n={len(Y):3d} const {b[0]:5.1f} strawBuyers {b[1]:+5.1f} wheatBuyers {b[2]:+5.2f}  R2 {r2:.2f}')
print('\nCarrots d8-15 ~ const + carrot buyers known d9 + carrot buyers known d12')
CB = A.CB
for g in ['Boey', 'FQ', 'TFC', 'CBF', 'Yiz']:
    X = []; Y = []
    for key, rows in A.seats[g]:
        X.append([1, A.nb(rows, 9, CB), A.nb(rows, 12, CB) - A.nb(rows, 9, CB)])
        Y.append(A.pl(rows, 'CARROT', 8, 15))
    b, r2 = lstsq(X, Y)
    print(f'  {g:5s} n={len(Y):3d} const {b[0]:5.1f} buyers@d9 {b[1]:+5.1f} newBuyer@d12 {b[2]:+5.1f}  R2 {r2:.2f}')
print('\nTomatoes d9-15 ~ const + tomato buyers known d9 + new by d12')
for g in ['CBF', 'TFC', 'Yiz', 'T7']:
    X = []; Y = []
    for key, rows in A.seats[g]:
        X.append([1, A.nb(rows, 9, A.TB), A.nb(rows, 12, A.TB) - A.nb(rows, 9, A.TB)])
        Y.append(A.pl(rows, 'TOMATO', 9, 15))
    b, r2 = lstsq(X, Y)
    print(f'  {g:5s} n={len(Y):3d} const {b[0]:5.1f} buyers@d9 {b[1]:+5.1f} newBuyer@d12 {b[2]:+5.1f}  R2 {r2:.2f}')
