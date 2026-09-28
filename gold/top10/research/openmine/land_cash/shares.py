"""Share of seats buying each animal kind / strawberry seeds on each day d0..d9 (>=1 unit), recorded elite 23-26 Sep + T7."""
import collections
from common import load, by_team, SHORT, TEAMS, pairs
S = load()
g = by_team(S, 'rec'); g['T7'] = [p[0] for p in pairs(S)]
for kind, key in (('COW', 'buy_animal'), ('SHEEP', 'buy_animal'), ('GOOSE', 'buy_animal'), ('STRAWBERRY', 'buy_seed'), ('MELON', 'buy_seed')):
    print('== %s: share of seats buying on day d (mean units when bought)' % kind)
    for t in TEAMS + ['T7']:
        ss = g[t]
        cells = []
        for d in range(10):
            xs = [(s['days'][d].get(key) or {}).get(kind, [0])[0] for s in ss]
            b = [x for x in xs if x > 0]
            cells.append('%3.0f%%(%.1f)' % (100 * len(b) / len(ss), sum(b) / len(b)) if b else '     -    ')
        print('  %-5s' % SHORT[t], ' '.join('%10s' % c for c in cells))
