"""Per-kind yield per animal-day (units harvested / placed animal-days), care and feed rate by kind, days 0-15 and 16-29."""
import collections
from lib import *
rows = load(role={'rec', 'ours'})
G = collections.defaultdict(list)
for r in rows:
    if r['role'] == 'rec' and late(r):
        G[SHORT[r['team']]].append(r)
    elif r['role'] == 'ours':
        G['T7'].append(r)
P = {'GOOSE': 'EGG', 'COW': 'MILK', 'SHEEP': 'WOOL'}
for g in ['Boey', 'FQ', 'CBF', 'Yiz', 'TFC', 'T7']:
    s = []
    for a0, a1 in ((0, 15), (16, 28)):
        for a in AN:
            ad = sum(r['days'][d]['herd'].get(a, 0) for r in G[g] for d in range(a0, a1 + 1))
            if not ad:
                continue
            u = sum(r['days'][d]['hv'].get(P[a], 0) for r in G[g] for d in range(a0, a1 + 1))
            fe = sum(r['days'][d]['feed'][a] for r in G[g] for d in range(a0, a1 + 1))
            ca = sum(r['days'][d]['care'][a] for r in G[g] for d in range(a0, a1 + 1))
            s.append('d%d-%d %s %.2f/ad feed %.0f%% care %.0f%%' % (a0, a1, a[0], u / ad, 100 * fe / ad, 100 * ca / ad))
    print('%-5s ' % g + ' | '.join(s))
