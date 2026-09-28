"""Leakage-free target mix: targets = mean tiles of top-30 winners in the 23-24 Sep corpora, keyed by the product's demand
among the shops known at the day (4 shops for days 12/16, 6 for days 20/24). Applied to the 25-26 Sep gate seats
(goldg + top10g): gap = target - sf8 (and target - repaired elite, as the out-of-sample check), grouped by town type
(the product with the largest known demand at 4 shops, and the yarn class). $/tile-day values from sf8's own gate rows.
usage: target_gap.py corpus_train1,... gate_diag1,... gate_refs1,..."""
import sys, json, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
corp = sys.argv[1].split(','); gd = sys.argv[2].split(','); gr = sys.argv[3].split(',')
T30 = set(top_teams(30))
W = list(corpus_seats(corp, T30, winners=True))
S = list(gate_seats(gd, gr))
led = {}
for g in ('goldg', 'top10g'):
    for x in map(json.loads, open('gold/top10/gates/' + g + '_sf8.jsonl', encoding='utf-8')): led[(x['gid'], x['seat'])] = x
KEYS = [('GOOSE', 'EGG', 12, 4), ('COW', 'MILK', 12, 4), ('SHEEP', 'WOOL', 12, 4), ('TOMATO', 'TOMATO', 16, 4), ('CARROT', 'CARROT', 16, 4),
        ('STRAWBERRY', 'STRAWBERRY', 20, 6), ('WHEAT', 'WHEAT', 20, 6), ('CARROT', 'CARROT', 24, 6), ('WHEAT', 'WHEAT', 24, 6)]
tab = collections.defaultdict(list)
for s in W:
    for tile, prod, d, k in KEYS: tab[(tile, d, min(dem(s['shops'][:k], prod), 24))].append(tiles(s['days'], d, tile))
def target(tile, prod, d, k, shops):
    b = min(dem(shops[:k], prod), 24)
    v = tab.get((tile, d, b)) or []
    while len(v) < 10 and b > 0:  # sparse cell: fall back to the next lower bucket
        b -= 6; v = tab.get((tile, d, b)) or []
    return sum(v) / len(v) if v else 0.0
def yarn_at(shops): return next((3 * (i + 1) for i, s in enumerate(shops) if s == 'YARN_STORE'), 99)
def ttype(shops):
    y = yarn_at(shops)
    yc = 'yarn<=d9' if y <= 9 else ('yarn d12-15' if y <= 15 else ('yarn d18-24' if y <= 24 else 'no yarn'))
    dd = {p: dem(shops[:4], p) for p in ('TOMATO', 'CARROT', 'EGG', 'MILK', 'STRAWBERRY')}
    top = max(dd, key=lambda p: dd[p])
    return yc, f'{top.lower()}-led' if dd[top] >= 12 else 'mixed/poor'
# $/tile-day (d12-28) from sf8 rows, all towns
val = {}
for tile, prod in (('GOOSE', 'EGG'), ('COW', 'MILK'), ('SHEEP', 'WOOL'), ('TOMATO', 'TOMATO'), ('CARROT', 'CARROT'), ('WHEAT', 'WHEAT'), ('STRAWBERRY', 'STRAWBERRY')):
    td = sum(sum(tiles(s['us'], d, tile) for d in range(12, 29)) for s in S)
    rv = sum(led[(s['gid'], s['seat'])]['led_us'].get(prod, 0) for s in S)
    val[tile] = rv / max(td, 1) if prod != 'WHEAT' else rv / max(td, 1)
print('ledger $ per tile-day (sf8, whole game revenue / tile-days d12-28; indicative only): ' + ' '.join(f'{k[:5]} {v:.0f}' for k, v in val.items()))
rows = []
for s in S:
    g_us = {f'{t}@{d}': target(t, p, d, k, s['shops']) - tiles(s['us'], d, t) for t, p, d, k in KEYS}
    g_el = {f'{t}@{d}': target(t, p, d, k, s['shops']) - tiles(s['elite'], d, t) for t, p, d, k in KEYS}
    L = led[(s['gid'], s['seat'])]
    rows.append(dict(yc=ttype(s['shops'])[0], lead=ttype(s['shops'])[1], gu=g_us, ge=g_el, m=L['m']))
cols = [f'{t}@{d}' for t, p, d, k in KEYS]
def show(title, keyf):
    print(f'\n== {title}: n, sf8 win%, margin | gap target - sf8 (target - repaired elite) in tiles ==')
    print(f"{'':24s} {'n':>4} {'win':>4} {'margin':>7} | " + ' '.join(f'{c[:5]+c[c.index("@"):]:>13s}' for c in cols))
    by = collections.defaultdict(list)
    for r in rows: by[keyf(r)].append(r)
    for k in sorted(by, key=lambda k: -len(by[k])):
        R = by[k]; n = len(R)
        print(f'{k:24s} {n:4d} {100*sum(r["m"]>0 for r in R)/n:4.0f} {sum(r["m"] for r in R)/n:+7.0f} | ' +
              ' '.join(f'{sum(r["gu"][c] for r in R)/n:+5.1f}({sum(r["ge"][c] for r in R)/n:+5.1f})' for c in cols))
show('all', lambda r: 'all')
show('yarn class', lambda r: r['yc'])
show('4-shop lead product', lambda r: r['lead'])
