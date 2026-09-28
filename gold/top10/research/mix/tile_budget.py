"""Tile budget by day: owned tiles (25 x quadrants, minus the 4 shed-access tiles? no: shed tiles are outside the grid
count here) split into strawberry, other crops, animals, empty structures, weeds and free, for corpus winners vs gate
elite vs sf8. Shows whether sf8's crop gap in controller days is free-tile choice or occupancy/land.
usage: tile_budget.py corpus1,... gate_diag1,... gate_refs1,..."""
import sys
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
corp = sys.argv[1].split(','); gd = sys.argv[2].split(','); gr = sys.argv[3].split(',')
T30 = set(top_teams(30))
W = [s['days'] for s in corpus_seats(corp, T30, winners=True)]
G = list(gate_seats(gd, gr)); E = [s['elite'] for s in G]; U = [s['us'] for s in G]
CR = ('WHEAT', 'CARROT', 'TOMATO', 'MELON'); AN = ('COW', 'SHEEP', 'GOOSE')
def nq(x, d): return 1 + sum(len(x[i]['land']) for i in range(d + 1))
def parts(x, d):
    t = x[d]['t']
    st = t.get('STRAWBERRY', 0); oc = sum(t.get(k, 0) for k in CR); an = sum(t.get(k, 0) for k in AN)
    es = t.get('PASTURE', 0) + t.get('COOP', 0); we = t.get('WEED', 0)
    own = 25 * nq(x, d)
    return own, st, oc, an, es, we, own - st - oc - an - es - we
print('day | group: owned  straw  other-crops  animals  empty-structs  weeds  free')
for d in (12, 14, 16, 18, 20, 22, 24, 26, 28):
    line = f'd{d:2d}'
    for nm, grp in (('W', W), ('E', E), ('U', U)):
        s = [sum(parts(x, d)[i] for x in grp) / len(grp) for i in range(7)]
        line += f' | {nm} ' + ' '.join(f'{v:4.1f}' for v in s)
    print(line)
