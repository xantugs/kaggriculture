"""Hour-0 prices of crops (days 0..16) in the recorded elite games vs the T7 games (same towns), and the rival's crop
tiles seen at hour 0. usage: a6_px.py"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a1_plant import G, AB, TEAMS

order = TEAMS + ['T7']
for item in ('STRAWBERRY', 'MELON', 'WHEAT', 'TOMATO', 'CARROT', 'FERTILIZER'):
    print(f'\n== {item} price at hour 0 (mean)')
    print('day ' + ''.join(f'{AB[t]:>8s}' for t in order))
    for d in (0, 3, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16):
        line = f'{d:3d} '
        for t in order:
            xs = [r[d]['px'][item] for r in G[t] if r[d] and r[d].get('px')]
            line += f'{sum(xs)/max(1,len(xs)):8.1f}'
        print(line)
print('\n== rival strawberry tiles at hour 0 (mean) | own')
for d in (4, 6, 8, 10, 12, 14, 16):
    line = f'{d:3d} '
    for t in order:
        xs = G[t]
        line += f'{sum((r[d]["riv_crops"] or {}).get("STRAWBERRY", 0) for r in xs)/len(xs):6.1f}/{sum((r[d]["crops"] or {}).get("STRAWBERRY", 0) for r in xs)/len(xs):4.1f}'
    print(line)
