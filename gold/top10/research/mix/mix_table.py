"""What winners grow, by the demand known at the decision day, vs sf8 in the gate towns.
usage: mix_table.py corpus_diag1.jsonl,... gate_diag1.jsonl,... gate_refs1.jsonl,...
Winners = seats of top-30 teams that won their game. Demand = daily units drained by the shops known at day D."""
import sys, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *

corp = sys.argv[1].split(','); gd = sys.argv[2].split(','); gr = sys.argv[3].split(',')
T30 = set(top_teams(30))
W = list(corpus_seats(corp, T30, winners=True))
G = list(gate_seats(gd, gr))
print(f'winners (top-30, won): {len(W)} seats; gate seats (sf8 vs elite): {len(G)}')
DAYS = (12, 16, 20, 24)
WIN = ((12, 16), (16, 20), (20, 24), (24, 30))
def mean(v): return sum(v) / len(v) if v else float('nan')
for prod in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'EGG', 'MILK', 'WOOL'):
    tile = TILE_OF[prod]
    for dday, k in ((12, 4), (18, 6)):
        bw = collections.defaultdict(list); bu = collections.defaultdict(list); be = collections.defaultdict(list)
        for s in W: bw[min(dem(s['shops'][:k], prod), 24)].append(s['days'])
        for s in G:
            b = min(dem(s['shops'][:k], prod), 24)
            bu[b].append(s['us']); be[b].append(s['elite'])
        print(f'\n{prod} ({tile}) by demand at {k} shops (day {dday}); cells: winners / gate elite / sf8')
        for b in sorted(set(bw) | set(bu)):
            ws, us, es = bw[b], bu[b], be[b]
            cells = ' '.join(f'd{d}:{mean([tiles(x, d, tile) for x in ws]):4.1f}/{mean([tiles(x, d, tile) for x in es]):4.1f}/{mean([tiles(x, d, tile) for x in us]):4.1f}' for d in DAYS)
            if tile in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'):
                cells += ' | pl ' + ' '.join(f'{a}-{c-1}:{mean([plantings(x, tile, a, c) for x in ws]):4.1f}/{mean([plantings(x, tile, a, c) for x in es]):4.1f}/{mean([plantings(x, tile, a, c) for x in us]):4.1f}' for a, c in WIN)
            print(f'  dem {b:2d} n {len(ws):4d}/{len(us):3d}  {cells}')
