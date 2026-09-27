"""No-yarn towns (no YARN_STORE among the first 3 shops, i.e. known when the tape buys its day 8-9 sheep): sheep counts,
wool units/revenue by window and by whether a yarn store appears later, winners vs gate elite vs sf8.
usage: sheep_noyarn.py corpus1,... gate_diag1,... gate_refs1,..."""
import sys, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
corp = sys.argv[1].split(','); gd = sys.argv[2].split(','); gr = sys.argv[3].split(',')
T30 = set(top_teams(30))
W = list(corpus_seats(corp, T30, winners=True)); G = list(gate_seats(gd, gr))
def yarn_at(shops):
    return next((3 * (i + 1) for i, s in enumerate(shops) if s == 'YARN_STORE'), 99)
WIN = ((0, 12), (12, 18), (18, 24), (24, 30))
for label, sel in (('no yarn by day 9, none later', lambda s: yarn_at(s) == 99), ('no yarn by day 9, yarn on day 12-15', lambda s: 12 <= yarn_at(s) <= 15),
                   ('no yarn by day 9, yarn on day 18-24', lambda s: 18 <= yarn_at(s) <= 24), ('yarn by day 9', lambda s: yarn_at(s) <= 9)):
    w = [s['days'] for s in W if sel(s['shops'])]; ge = [s['elite'] for s in G if sel(s['shops'])]; gu = [s['us'] for s in G if sel(s['shops'])]
    print(f'\n{label}: n winners {len(w)}, gate {len(gu)}')
    for nm, grp in (('winners', w), ('gate elite', ge), ('sf8', gu)):
        if not grp: continue
        sh = ' '.join(f'd{d}:{sum(tiles(x, d, "SHEEP") for x in grp)/len(grp):4.1f}' for d in (7, 9, 11, 16, 24))
        wl = ' '.join(f"{a}-{b-1}: {sum(sum(x[d]['su'].get('WOOL', 0) for d in range(a, b)) for x in grp)/len(grp):4.0f}u ${sum(sum(x[d]['sd'].get('WOOL', 0) for d in range(a, b)) for x in grp)/len(grp):5.0f}" for a, b in WIN)
        print(f'  {nm:10s} sheep {sh} | wool {wl}')
