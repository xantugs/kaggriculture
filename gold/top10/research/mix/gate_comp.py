"""Composition (end-of-day tiles) and plantings of sf8 vs the repaired elite in the elite's own town, from wheat_diag
cand-mode rows. usage: gate_comp.py diag.jsonl[,diag2.jsonl] refs1[,refs2]"""
import json, sys, collections
SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"], "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
         "YARN_STORE": ["WOOL"], "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
         "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
def dem(shops, p): return sum((12 if len(SHOPS[s]) == 1 else 6) for s in shops if p in SHOPS[s])
K = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'COW', 'SHEEP', 'GOOSE']
rows = []
refs = {}
for f in sys.argv[2].split(','):
    for r in map(json.loads, open(f, encoding='utf-8')): refs[(r['gid'], r['seat'])] = r
for f in sys.argv[1].split(','):
    for x in map(json.loads, open(f, encoding='utf-8')):
        x['shops'] = refs[(x['gid'], x['seat'])]['shops']; rows.append(x)
print(len(rows), 'seats; sf8 wins', sum(x['m'] > 0 for x in rows))
def tiles(side, d): return side[d]['tiles']
for grp, sel in (('all', lambda x: True), ('elite won', lambda x: x['m'] < 0), ('sf8 won', lambda x: x['m'] > 0)):
    R = [x for x in rows if sel(x)]
    print(f'\n== {grp} (n {len(R)}): end-of-day tiles elite / sf8 ==')
    for d in (6, 9, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28):
        print(f'day {d:2d} ' + ' '.join(f"{k[:5]:5s} {sum(tiles(x['elite'], d).get(k, 0) for x in R)/len(R):4.1f}/{sum(tiles(x['other'], d).get(k, 0) for x in R)/len(R):4.1f}" for k in K))
    print('plantings by window elite / sf8')
    for a, b in ((0, 6), (6, 12), (12, 16), (16, 20), (20, 24), (24, 30)):
        def pl(side, k): return sum(sum(v for kk, v in side[d]['plant'].items() if kk.startswith(k + '@')) for d in range(a, b))
        print(f'days {a:2d}-{b-1:2d} ' + ' '.join(f"{k[:5]:5s} {sum(pl(x['elite'], k) for x in R)/len(R):5.1f}/{sum(pl(x['other'], k) for x in R)/len(R):5.1f}" for k in K[:5]))
    print('hires per day elite / sf8: ' + ' '.join(f"{d}:{sum(x['elite'][d]['hires'] for x in R)/len(R):.1f}/{sum(x['other'][d]['hires'] for x in R)/len(R):.1f}" for d in range(0, 30, 2)))
    print('land day elite / sf8: ', collections.Counter((q, d) for x in R for d in range(30) for q in x['elite'][d]['land']).most_common(8), '|',
          collections.Counter((q, d) for x in R for d in range(30) for q in x['other'][d]['land']).most_common(8))
