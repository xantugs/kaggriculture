"""Revenue and realised unit price per product by day window, winners (corpus) vs gate elite vs sf8, by the product's
demand at 4 shops. usage: rev_windows.py corpus1,... gate_diag1,... gate_refs1,... [PROD,...]"""
import sys, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
corp = sys.argv[1].split(','); gd = sys.argv[2].split(','); gr = sys.argv[3].split(',')
prods = sys.argv[4].split(',') if len(sys.argv) > 4 else ['CARROT', 'TOMATO', 'WHEAT', 'EGG', 'STRAWBERRY', 'MILK', 'WOOL']
T30 = set(top_teams(30))
W = list(corpus_seats(corp, T30, winners=True)); G = list(gate_seats(gd, gr))
WIN = ((0, 12), (12, 16), (16, 20), (20, 24), (24, 30))
def agg(days, p, a, b):
    u = sum(days[d]['su'].get(p, 0) for d in range(a, b)); r = sum(days[d]['sd'].get(p, 0) for d in range(a, b))
    return u, r
for p in prods:
    print(f'\n{p}: revenue $ (units, $/unit) per window: winners | gate elite | sf8, by demand at 4 shops')
    bw = collections.defaultdict(list); bg = collections.defaultdict(list)
    for s in W: bw[min(dem(s['shops'][:4], p), 24)].append(s['days'])
    for s in G: bg[min(dem(s['shops'][:4], p), 24)].append(s)
    for b in sorted(set(bw) | set(bg)):
        line = f'  dem {b:2d} n{len(bw[b]):4d}/{len(bg[b]):3d} '
        for a, c in WIN:
            cells = []
            for grp in (bw[b], [s['elite'] for s in bg[b]], [s['us'] for s in bg[b]]):
                if not grp: cells.append('   -'); continue
                U = sum(agg(x, p, a, c)[0] for x in grp) / len(grp); R = sum(agg(x, p, a, c)[1] for x in grp) / len(grp)
                cells.append(f'{R:5.0f}({U:4.0f},{R/max(U,1e-9):3.0f})')
            line += f'| {a}-{c-1}: ' + ' '.join(cells) + ' '
        print(line)
