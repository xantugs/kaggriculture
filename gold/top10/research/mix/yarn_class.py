"""Gate seats (sf8 vs repaired elite) and corpus winners by yarn timing: margin, win%, ledgers (wool, anim, fert, milk, egg),
sheep counts and wool units. usage: yarn_class.py gate_diag1,... gate_refs1,... corpus1,..."""
import sys, json, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
gd = sys.argv[1].split(','); gr = sys.argv[2].split(','); corp = sys.argv[3].split(',')
G = 'gold/top10/gates/'
led = {}
for g in ('goldg', 'top10g'):
    for x in map(json.loads, open(G + g + '_sf8.jsonl', encoding='utf-8')): led[(x['gid'], x['seat'])] = x
S = list(gate_seats(gd, gr))
def yarn_at(shops): return next((3 * (i + 1) for i, s in enumerate(shops) if s == 'YARN_STORE'), 99)
def cls(shops):
    y = yarn_at(shops)
    return 'A yarn<=d9' if y <= 9 else ('B yarn d12-15' if y <= 15 else ('C yarn d18-24' if y <= 24 else 'D no yarn'))
PR = ['WOOL', 'MILK', 'EGG', 'FERTILIZER', 'WHEAT', 'anim', 'hire']
by = collections.defaultdict(list)
for s in S:
    s['led'] = led[(s['gid'], s['seat'])]; by[cls(s['shops'])].append(s)
print('gate seats by yarn timing (sheep us/elite at d11, d20; wool units sold us/elite; ledger us-elite)')
for c in sorted(by):
    R = by[c]; n = len(R)
    def m(f): return sum(f(x) for x in R) / n
    print(f"{c:14s} n{n:4d} win {100*m(lambda x: x['led']['m'] > 0):3.0f}% margin {m(lambda x: x['led']['m']):+6.0f} | sheep d11 {m(lambda x: tiles(x['us'], 11, 'SHEEP')):4.1f}/{m(lambda x: tiles(x['elite'], 11, 'SHEEP')):4.1f} d20 {m(lambda x: tiles(x['us'], 20, 'SHEEP')):4.1f}/{m(lambda x: tiles(x['elite'], 20, 'SHEEP')):4.1f} "
          f"cows d11 {m(lambda x: tiles(x['us'], 11, 'COW')):4.1f}/{m(lambda x: tiles(x['elite'], 11, 'COW')):4.1f} geese {m(lambda x: tiles(x['us'], 11, 'GOOSE')):3.1f}/{m(lambda x: tiles(x['elite'], 11, 'GOOSE')):3.1f} | wool u {m(lambda x: sum(d['su'].get('WOOL', 0) for d in x['us'])):4.0f}/{m(lambda x: sum(d['su'].get('WOOL', 0) for d in x['elite'])):4.0f} | "
          + ' '.join(f"{p[:4]} {m(lambda x: x['led']['led_us'].get(p, 0) - x['led']['led_elite'].get(p, 0)):+6.0f}" for p in PR)
          + f" | us wool$ {m(lambda x: x['led']['led_us'].get('WOOL', 0)):5.0f} el wool$ {m(lambda x: x['led']['led_elite'].get('WOOL', 0)):5.0f}")
T30 = set(top_teams(30))
W = list(corpus_seats(corp, T30, winners=False))
byc = collections.defaultdict(list)
for s in W: byc[cls(s['shops'])].append(s)
print('\ncorpus top-30 seats by yarn timing: win% by sheep count at d11 (<=3 / 4-5 / 6+), wool $')
for c in sorted(byc):
    R = byc[c]
    b = collections.defaultdict(list)
    for s in R:
        k = tiles(s['days'], 11, 'SHEEP'); b['<=3' if k <= 3 else ('4-5' if k <= 5 else '6+')].append(s)
    print(f"{c:14s} n{len(R):5d} " + ' '.join(f"{k}: n{len(v):4d} win {100*sum(x['won'] for x in v)/len(v):3.0f}% wool\$ {sum(sum(d['sd'].get('WOOL', 0) for d in x['days']) for x in v)/len(v):5.0f}" for k, v in sorted(b.items())))
