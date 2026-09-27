"""Revenue gap (us - elite) per product on the goldg/top10g sf8 gate rows, split by the demand for the product among the
shops known at day 12 (4 shops) and day 18 (6 shops). usage: gate_gap.py"""
import json, collections, sys
G = 'gold/top10/gates/'
SHOPS = {"BAKERY": ["EGG", "WHEAT"], "PIZZA_SHOP": ["MILK", "TOMATO", "WHEAT"], "BRUNCH_SPOT": ["EGG", "WHEAT", "STRAWBERRY"],
         "YARN_STORE": ["WOOL"], "ICE_CREAM_SHOP": ["STRAWBERRY", "MILK", "WHEAT"], "PET_CAFE": ["CARROT"],
         "SMOOTHIE_SHOP": ["STRAWBERRY", "MILK"], "FARMERS_MARKET": ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY"]}
def dem(shops, p): return sum((12 if len(SHOPS[s]) == 1 else 6) for s in shops if p in SHOPS[s])
rows = []
for g in ('goldg', 'top10g'):
    refs = {(r['gid'], r['seat']): r for r in map(json.loads, open(G + g + '_refs.jsonl', encoding='utf-8'))}
    for x in map(json.loads, open(G + g + '_sf8.jsonl', encoding='utf-8')):
        x['shops'] = refs[(x['gid'], x['seat'])]['shops']; x['g'] = g; rows.append(x)
print(len(rows), 'rows')
PR = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'EGG', 'MILK', 'WOOL', 'MELON', 'FERTILIZER']
for k in (4, 6):
    print(f'\n== gap us-elite by the product demand among the first {k} shops (mean $/seat, n) ==')
    for p in PR:
        b = collections.defaultdict(list)
        for x in rows:
            d = min(dem(x['shops'][:k], p), 24)
            b[d].append(x['led_us'].get(p, 0) - x['led_elite'].get(p, 0))
        print(f'{p:10s} ' + '  '.join(f'd{d:2d}: {sum(v)/len(v):+6.0f} (n{len(v):3d})' for d, v in sorted(b.items())))
# wins by demand buckets
print('\n== win rate and margin by tomato/carrot/wheat demand at 6 shops ==')
for p in ('TOMATO', 'CARROT', 'WHEAT', 'STRAWBERRY', 'EGG'):
    b = collections.defaultdict(list)
    for x in rows: b[min(dem(x['shops'][:6], p), 24)].append(x['m'])
    print(f'{p:10s} ' + '  '.join(f'd{d:2d}: W{100*sum(m>0 for m in v)/len(v):3.0f}% {sum(v)/len(v):+6.0f} (n{len(v)})' for d, v in sorted(b.items())))
