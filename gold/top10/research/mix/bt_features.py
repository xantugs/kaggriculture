"""Within-game, team-controlled association of composition with the margin, on top-30-vs-top-30 corpus games.
margin(seat0 - seat1) = fe(team0) - fe(team1) + sum_k beta_k * (x_k(seat0) - x_k(seat1)) + e
Both seats share the town, so town effects cancel; team fixed effects absorb team strength.
usage: bt_features.py corpus1,... [label]"""
import sys, json, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
T30 = set(top_teams(30))
def yarn_at(shops): return next((3 * (i + 1) for i, s in enumerate(shops) if s == 'YARN_STORE'), 99)
def feats(days, shops):
    ny = yarn_at(shops) > 9
    f = collections.OrderedDict()
    f['goose_d12'] = tiles(days, 12, 'GOOSE')
    f['cow_d12'] = tiles(days, 12, 'COW')
    f['sheep_d11_noyarn9'] = tiles(days, 11, 'SHEEP') if ny else 0
    f['sheep_d11_yarn9'] = tiles(days, 11, 'SHEEP') if not ny else 0
    f['straw_d12'] = tiles(days, 12, 'STRAWBERRY')
    f['tomato_d16'] = tiles(days, 16, 'TOMATO')
    f['wheat_d20'] = tiles(days, 20, 'WHEAT')
    f['carrot_d20'] = tiles(days, 20, 'CARROT')
    f['wheat_pl_24_29'] = plantings(days, 'WHEAT', 24, 30)
    f['carrot_pl_24_29'] = plantings(days, 'CARROT', 24, 30)
    f['melon_pl'] = plantings(days, 'MELON', 0, 30)
    f['quads_d12'] = 1 + sum(len(days[d]['land']) for d in range(13))
    f['hires_12_29'] = sum(days[d]['h'] for d in range(12, 30))
    return f
G = []
for p in sys.argv[1].split(','):
    for l in open(p, encoding='utf-8'):
        g = json.loads(l)
        if not g.get('ok') or None in g['rew']: continue
        if g['names'][0] in T30 and g['names'][1] in T30 and g['names'][0] != g['names'][1]:
            G.append((g['names'], g['rew'], feats(g['f'][0], g['shops']), feats(g['f'][1], g['shops'])))
teams = sorted({t for n, _, _, _ in G for t in n})
ref = max(teams, key=lambda t: sum(t in n for n, _, _, _ in G))
tcols = [t for t in teams if t != ref]
K = list(G[0][2].keys())
X, y = [], []
for n, r, f0, f1 in G:
    row = [0.0] * len(tcols)
    for s, t in ((1.0, n[0]), (-1.0, n[1])):
        if t != ref: row[tcols.index(t)] += s
    row += [f0[k] - f1[k] for k in K]
    X.append(row); y.append(r[0] - r[1])
b, se = ols(X, y)
lab = sys.argv[2] if len(sys.argv) > 2 else ''
print(f'{lab} games {len(G)}, teams {len(teams)} (ref {ref}); margin beta per unit (+- se), with team fixed effects')
for k, bi, si in zip(K, b[len(tcols):], se[len(tcols):]):
    print(f'  {k:18s} {bi:+8.0f} +- {si:5.0f}  (t {bi/max(si,1e-9):+5.1f})')
# without team FE for comparison
b2, se2 = ols([row[len(tcols):] for row in X], y)
print('  (no team FE: ' + ' '.join(f'{k}={v:+.0f}' for k, v in zip(K, b2)) + ')')
