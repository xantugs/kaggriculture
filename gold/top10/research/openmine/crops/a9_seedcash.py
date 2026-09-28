"""Seed spend, strawberry seeds, hour-0 cash and the day's lowest cash (days 0..11); sells and hires (days 0..9).
usage: a9_seedcash.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from a1_plant import G, AB, TEAMS
order = TEAMS + ['T7']
print('seed $ by day (all crops) | strawberry seeds units | cash m0 | mmin   (means per seat)')
print('day ' + ''.join(f'{AB[t]:>34s}' for t in order))
for d in range(0, 12):
    line = f'{d:3d} '
    for t in order:
        xs = [r[d] for r in G[t]]
        sd = sum(sum(v[1] for v in (x['buy_seed'] or {}).values()) for x in xs) / len(xs)
        su = sum(((x['buy_seed'] or {}).get('STRAWBERRY') or [0])[0] for x in xs) / len(xs)
        m0 = sum(x['m0'] for x in xs) / len(xs); mm = sum(x['mmin'] for x in xs) / len(xs)
        line += f'  ${sd:5.0f} S{su:4.1f} m0 {m0:5.0f} min {mm:5.0f}'
    print(line)
print('\nday: sells $ (all) | hires  (means per seat)')
for d in range(0, 10):
    line = f'{d:3d} '
    for t in order:
        xs = [r[d] for r in G[t]]
        se = sum(sum(v[1] for v in (x['sell'] or {}).values()) for x in xs) / len(xs)
        h = sum(x['hires'] for x in xs) / len(xs)
        line += f' | {AB[t]:4s} sell {se:5.0f} h {h:4.1f}'
    print(line)
