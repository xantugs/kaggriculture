"""Within-game winner-minus-loser composition (both seats top-30 teams, same town), by the demand for the product known at
the decision day. Also the win rate of the seat that has more of X (sign test), and avg price realised per product.
usage: paired_wl.py corpus_diag1.jsonl,..."""
import sys, json, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
T30 = set(top_teams(30))
G = []
for p in sys.argv[1].split(','):
    for l in open(p, encoding='utf-8'):
        g = json.loads(l)
        if not g.get('ok') or None in g['rew']: continue
        if g['names'][0] in T30 and g['names'][1] in T30 and g['rew'][0] != g['rew'][1]:
            G.append(g)
print('top30-vs-top30 games', len(G))
def feats(days):
    f = {}
    f['wheat_pl_12_15'] = plantings(days, 'WHEAT', 12, 16); f['wheat_pl_16_23'] = plantings(days, 'WHEAT', 16, 24); f['wheat_pl_24_29'] = plantings(days, 'WHEAT', 24, 30)
    f['carrot_pl_12_15'] = plantings(days, 'CARROT', 12, 16); f['carrot_pl_16_23'] = plantings(days, 'CARROT', 16, 24); f['carrot_pl_24_29'] = plantings(days, 'CARROT', 24, 30)
    f['tomato_pl_6_11'] = plantings(days, 'TOMATO', 6, 12); f['tomato_pl_12_15'] = plantings(days, 'TOMATO', 12, 16); f['tomato_pl_16_19'] = plantings(days, 'TOMATO', 16, 20)
    f['straw_pl_0_11'] = plantings(days, 'STRAWBERRY', 0, 12); f['straw_pl_12_15'] = plantings(days, 'STRAWBERRY', 12, 16)
    f['melon_pl'] = plantings(days, 'MELON', 0, 30)
    for k in ('GOOSE', 'COW', 'SHEEP'):
        f[k.lower() + '_d12'] = tiles(days, 12, k); f[k.lower() + '_d20'] = tiles(days, 20, k)
    f['hires_12_29'] = sum(days[d]['h'] for d in range(12, 30)); f['hire$_12_29'] = sum(days[d]['hc'] for d in range(12, 30))
    f['land_n'] = sum(len(days[d]['land']) for d in range(30))
    f['sw_day'] = next((d for d in range(30) if 'SW' in days[d]['land']), 99)
    return f
KEYS = list(feats(G[0]['f'][0]).keys())
BUCK = {'wheat': 'WHEAT', 'carrot': 'CARROT', 'tomato': 'TOMATO', 'straw': 'STRAWBERRY', 'goose': 'EGG', 'cow': 'MILK', 'sheep': 'WOOL', 'melon': None, 'hires': None, 'hire$': None, 'land': None, 'sw': None}
print('\nfeature: mean winner-loser diff overall; by demand (4 shops) for the feature product: diff (P(winner has more | differ), n)')
for k in KEYS:
    prod = BUCK[k.split('_')[0]]
    b = collections.defaultdict(list)
    for g in G:
        w = 0 if g['rew'][0] > g['rew'][1] else 1
        fw, fl = feats(g['f'][w]), feats(g['f'][1 - w])
        key = min(dem(g['shops'][:4], prod), 24) if prod else 'all'
        b[key].append(fw[k] - fl[k]); b['ALL'].append(fw[k] - fl[k])
    def cell(v):
        nz = [x for x in v if x != 0]
        return f'{sum(v)/len(v):+5.1f} ({100*sum(x>0 for x in nz)/max(1,len(nz)):3.0f}% n{len(v)})'
    print(f'{k:16s} ALL {cell(b["ALL"])} | ' + '  '.join(f'd{kk}: {cell(v)}' for kk, v in sorted(((kk, v) for kk, v in b.items() if kk not in ('ALL', 'all')), key=lambda kv: kv[0])))
