"""Animals on the farm by day, winners (corpus) vs gate elite vs sf8, by the product demand known at day k*3.
usage: herd_days.py corpus1,... gate_diag1,... gate_refs1,... [nshops]"""
import sys, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
corp = sys.argv[1].split(','); gd = sys.argv[2].split(','); gr = sys.argv[3].split(',')
k = int(sys.argv[4]) if len(sys.argv) > 4 else 3
T30 = set(top_teams(30))
W = list(corpus_seats(corp, T30, winners=True)); G = list(gate_seats(gd, gr))
for prod, an in (('MILK', 'COW'), ('EGG', 'GOOSE'), ('WOOL', 'SHEEP')):
    print(f'\n{an} count at end of day, by {prod} demand at {k} shops: winners / gate elite / sf8')
    bw = collections.defaultdict(list); bg = collections.defaultdict(list)
    for s in W: bw[min(dem(s['shops'][:k], prod), 24)].append(s['days'])
    for s in G: bg[min(dem(s['shops'][:k], prod), 24)].append(s)
    for b in sorted(set(bw) | set(bg)):
        def m(grp, d): return sum(tiles(x, d, an) for x in grp) / len(grp) if grp else float('nan')
        E = [s['elite'] for s in bg[b]]; U = [s['us'] for s in bg[b]]
        print(f'  dem {b:2d} n{len(bw[b]):4d}/{len(bg[b]):3d} ' + ' '.join(f'd{d}:{m(bw[b], d):4.1f}/{m(E, d):4.1f}/{m(U, d):4.1f}' for d in (2, 5, 7, 9, 11, 12, 14, 16, 20, 24)))
