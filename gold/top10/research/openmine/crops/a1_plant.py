"""Plantings by day and crop (days 0..15), tiles held at hour 0, seeds bought; per team (recorded, 23-26 Sep) vs T7.
usage: a1_plant.py [date_min]"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load import days

DMIN = sys.argv[1] if len(sys.argv) > 1 else '2026-09-23'
D = days()
CR = ('WHEAT', 'STRAWBERRY', 'MELON', 'TOMATO', 'CARROT')
TEAMS = ['Boey', 'Fourth Quadrant', '吃白饭的大肥鱼', 'THIRD FARM CLUB', 'Yizhou']
AB = {'Boey': 'Boey', 'Fourth Quadrant': 'FQ', '吃白饭的大肥鱼': 'CBF', 'THIRD FARM CLUB': 'TFC', 'Yizhou': 'Yiz', 'T7': 'T7'}


def groups():
    g = collections.defaultdict(list)
    for key, rows in D['days'].items():
        role, gid, seat = key
        m = D['meta'][key]
        if role == 'rec' and m['date'] >= DMIN:
            g[m['team']].append(rows)
        elif role == 'ours':
            g['T7'].append(rows)
            g['T7 vs ' + AB[m['opp']]].append(rows)
    return g


def plants(row, crop):
    return sum(v for k, v in (row.get('ops') or {}).items() if k.startswith('PLANT:' + crop))


G = groups()
if __name__ == '__main__':
    order = TEAMS + ['T7']
    print('seats:', {AB[k]: len(G[k]) for k in order})
    for crop in CR:
        print(f'\n== {crop}: mean plantings per seat by day (share of seats planting >0 in brackets)')
        print('day  ' + ''.join(f'{AB[t]:>13s}' for t in order))
        for d in range(16):
            line = f'{d:3d}  '
            for t in order:
                xs = [plants(r[d], crop) for r in G[t] if r[d]]
                n = len(xs)
                line += f'{sum(xs)/n:7.1f} ({100*sum(x>0 for x in xs)/n:3.0f})'
            print(line)
        tot = '0-15 '
        for t in order:
            xs = [sum(plants(r[d], crop) for d in range(16) if r[d]) for r in G[t]]
            tot += f'{sum(xs)/len(xs):13.1f}'
        print(tot)

    print('\n== tiles held at hour 0 (mean per seat): W S M T C | free weeds')
    for d in (1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16):
        line = f'd{d:2d} '
        for t in order:
            xs = G[t]
            v = [sum((r[d]['crops'] or {}).get(c, 0) for r in xs) / len(xs) for c in CR]
            line += ' | ' + ' '.join(f'{x:4.1f}' for x in v)
        print(line)
    print('     ' + ''.join(f' | {AB[t]:^24s}' for t in order))

