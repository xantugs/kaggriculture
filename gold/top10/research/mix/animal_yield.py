"""Realised product revenue per productive animal-day (days 12-29), by yarn timing class, for sf8 and the repaired elite on
the gate seats, and for corpus winners. Productive animal-days = sum over days 12-28 of end-of-day animal count.
usage: animal_yield.py gate_diag1,... gate_refs1,... corpus1,..."""
import sys, collections
sys.path.insert(0, 'gold/top10/research/mix')
from mixlib import *
gd = sys.argv[1].split(','); gr = sys.argv[2].split(','); corp = sys.argv[3].split(',')
def yarn_at(shops): return next((3 * (i + 1) for i, s in enumerate(shops) if s == 'YARN_STORE'), 99)
def cls(shops):
    y = yarn_at(shops)
    return 'A yarn<=d9' if y <= 9 else ('B yarn d12-15' if y <= 15 else ('C yarn d18-24' if y <= 24 else 'D no yarn'))
def egg_cls(shops): return 'egg shop by d9' if any(s in ('BAKERY', 'BRUNCH_SPOT') for s in shops[:3]) else 'no egg shop by d9'
S = list(gate_seats(gd, gr))
T30 = set(top_teams(30))
W = list(corpus_seats(corp, T30, winners=True))
AN = (('SHEEP', 'WOOL'), ('GOOSE', 'EGG'), ('COW', 'MILK'))
def ad(days, an, a=12, b=29): return sum(tiles(days, d, an) for d in range(a, b))
def rev(days, p, a=12, b=30): return sum(days[d]['sd'].get(p, 0) for d in range(a, b))
def units(days, p, a=12, b=30): return sum(days[d]['su'].get(p, 0) for d in range(a, b))
for keyf, nm in ((cls, 'yarn class'), (egg_cls, 'egg class')):
    print(f'\n== by {nm}: $ per animal-day d12-29 (units/animal-day, $/unit) for sf8 | gate elite | corpus winners ==')
    groups = collections.defaultdict(lambda: collections.defaultdict(list))
    for s in S:
        groups[keyf(s['shops'])]['sf8'].append(s['us']); groups[keyf(s['shops'])]['elite'].append(s['elite'])
    for s in W: groups[keyf(s['shops'])]['winners'].append(s['days'])
    for c in sorted(groups):
        line = f'{c:18s}'
        for an, p in AN:
            cells = []
            for g in ('sf8', 'elite', 'winners'):
                R = groups[c][g]
                A = sum(ad(x, an) for x in R); Rv = sum(rev(x, p) for x in R); U = sum(units(x, p) for x in R)
                cells.append(f'{Rv/max(A,1):4.0f}({U/max(A,1):.2f},{Rv/max(U,1):3.0f})')
            line += f' | {an[:5]} ' + ' '.join(cells)
        line += f" | n {len(groups[c]['sf8'])}/{len(groups[c]['winners'])}"
        print(line)
