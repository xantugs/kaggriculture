"""Where: plantings by crop x quadrant in day windows, and the hour-0 tile budget per quadrant (crops, animals, empty
structures, weeds, free) on selected days. Team (recorded, 23-26 Sep) vs T7.
usage: a2_quad.py"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from load import days
from a1_plant import G, AB, TEAMS, CR

order = TEAMS + ['T7']
WIN = [(0, 0), (1, 2), (3, 5), (6, 7), (8, 9), (10, 11), (12, 13), (14, 15)]
QS = ('NW', 'NE', 'SW', 'SE')
print('== plantings per seat by crop@quadrant and day window')
for crop in CR:
    print(f'\n-- {crop}')
    print('window   ' + ''.join(f'{AB[t]:>22s}' for t in order))
    print('         ' + ''.join(f'{"NW  NE  SW  SE":>22s}' for t in order))
    for a, b in WIN:
        line = f'd{a:2d}-{b:2d}   '
        for t in order:
            xs = G[t]; n = len(xs)
            v = []
            for Q in QS:
                s = 0
                for r in xs:
                    for d in range(a, b + 1):
                        s += (r[d]['ops'] or {}).get(f'PLANT:{crop}@{Q}', 0)
                v.append(s / n)
            line += '  ' + ' '.join(f'{x:4.1f}' for x in v) + '   '
        print(line)

print('\n== hour-0 tile budget per quadrant (mean per seat; seats that own the quadrant): '
      'W S M T C | cow sheep goose | emptyStruct weed free')
for d in (4, 6, 8, 10, 12, 14, 16):
    print(f'\n-- day {d}')
    for t in order:
        xs = G[t]
        for Q in QS:
            own = [r for r in xs if r[d]['q'] and Q in r[d]['q']]
            if not own:
                continue
            n = len(own)
            def m(k):
                return sum((r[d]['q'][Q].get(k, 0)) for r in own) / n
            cr = [m('P:' + c) for c in CR]
            an = [m('A:COW'), m('A:SHEEP'), m('A:GOOSE')]
            es = m('COOP') + m('PASTURE')
            print(f'  {AB[t]:5s} {Q} own {100*n/len(xs):3.0f}% | ' + ' '.join(f'{x:4.1f}' for x in cr) + ' | ' +
                  ' '.join(f'{x:4.1f}' for x in an) + f' | {es:4.1f} {m("WEED"):4.1f} {m("free"):4.1f}')
