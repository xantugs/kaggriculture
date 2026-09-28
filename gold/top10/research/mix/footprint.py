"""Tiles in use by day (crops by kind + animals) and quadrants owned: winners (corpus) vs gate elite vs sf8.
usage: footprint.py corpus1,... gate_diag1,... gate_refs1,..."""
import sys, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
corp = sys.argv[1].split(','); gd = sys.argv[2].split(','); gr = sys.argv[3].split(',')
T30 = set(top_teams(30))
W = [s['days'] for s in corpus_seats(corp, T30, winners=True)]
L = [s['days'] for s in corpus_seats(corp, T30, winners=False) if not s['won']]
G = list(gate_seats(gd, gr))
E = [s['elite'] for s in G]; U = [s['us'] for s in G]
CR = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON']; AN = ['COW', 'SHEEP', 'GOOSE']
def m(grp, f): return sum(f(x) for x in grp) / len(grp)
def nq(x, d): return 1 + sum(len(x[i]['land']) for i in range(d + 1))
print(f'n winners {len(W)} losers {len(L)} gate {len(G)}')
for d in (6, 9, 12, 14, 16, 18, 20, 22, 24, 26, 28):
    line = f'd{d:2d} '
    for nm, grp in (('W', W), ('L', L), ('E', E), ('U', U)):
        crops = m(grp, lambda x: sum(x[d]['t'].get(k, 0) for k in CR)); an = m(grp, lambda x: sum(x[d]['t'].get(k, 0) for k in AN))
        line += f'| {nm} crops {crops:4.1f} anim {an:4.1f} q {m(grp, lambda x: nq(x, d)):3.1f} '
    print(line)
print('\nper crop tiles by day W / L / E / U')
for d in (12, 16, 18, 20, 22, 24, 26):
    print(f'd{d:2d} ' + ' '.join(f"{k[:5]} {m(W, lambda x: x[d]['t'].get(k, 0)):4.1f}/{m(L, lambda x: x[d]['t'].get(k, 0)):4.1f}/{m(E, lambda x: x[d]['t'].get(k, 0)):4.1f}/{m(U, lambda x: x[d]['t'].get(k, 0)):4.1f}" for k in CR + AN))
print('\nplantings per window W / L / E / U')
for a, b in ((0, 6), (6, 12), (12, 16), (16, 20), (20, 24), (24, 30)):
    print(f'{a:2d}-{b-1:2d} ' + ' '.join(f"{k[:5]} {m(W, lambda x: plantings(x, k, a, b)):5.1f}/{m(L, lambda x: plantings(x, k, a, b)):5.1f}/{m(E, lambda x: plantings(x, k, a, b)):5.1f}/{m(U, lambda x: plantings(x, k, a, b)):5.1f}" for k in CR))
print('\nhires per day W / L / E / U: ' + ' '.join(f"{d}:{m(W, lambda x: x[d]['h']):.1f}/{m(L, lambda x: x[d]['h']):.1f}/{m(E, lambda x: x[d]['h']):.1f}/{m(U, lambda x: x[d]['h']):.1f}" for d in range(0, 30, 3)))
print('hire $ days 12-29 W / L / E / U: ' + ' / '.join(f"{m(g, lambda x: sum(x[d]['hc'] for d in range(12, 30))):.0f}" for g in (W, L, E, U)))
print('revenue by product (total $) W / L / E / U')
for p in PRODS + ['MELON', 'FERTILIZER']:
    print(f'  {p:10s} ' + ' / '.join(f"{m(g, lambda x: sum(x[d]['sd'].get(p, 0) for d in range(30))):6.0f}" for g in (W, L, E, U)) +
          '   d16-29: ' + ' / '.join(f"{m(g, lambda x: sum(x[d]['sd'].get(p, 0) for d in range(16, 30))):6.0f}" for g in (W, L, E, U)))
