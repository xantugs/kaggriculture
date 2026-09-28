"""Show per-unit command timelines for one day of a tape_trace dump. usage: show_day.py trace.json day [side]"""
import sys, json
tr = json.load(open(sys.argv[1]))
day = int(sys.argv[2]); side = int(sys.argv[3]) if len(sys.argv) > 3 else 0
T = tr['tr']
AB = {'MOVE': '', 'NORTH': 'n', 'SOUTH': 's', 'EAST': 'e', 'WEST': 'w', 'PASS': '.', 'FEED': 'F', 'CARE': 'C', 'HARVEST': 'H',
      'COLLECT_FERTILIZER': 'X', 'PLACE': 'D', 'PICKUP': 'U', 'WATER': 'W', 'PLANT': 'P', 'DIG': 'G', 'BUILD_PASTURE': 'B', 'BUILD_COOP': 'b'}
nun = max(len(T[str(t)][side]['cmd']) for t in range(day * 24, day * 24 + 24) if str(t) in T)
for u in range(nun):
    line = []
    for t in range(day * 24, day * 24 + 24):
        e = T.get(str(t))
        if not e or u >= len(e[side]['cmd']): line.append(' '); continue
        c = e[side]['cmd'][u]
        s = AB.get(c[0], '?')
        if c[0] in ('PLACE', 'PICKUP'): s += c[1][:2].lower()
        if c[0] == 'DROP': s = 'DR'
        if c[0] == 'FERTILIZE': s = 'Z'
        line.append(s)
    print(f"u{u:2d} " + '|'.join(f"{x:>3s}" for x in line))
print('hr  ' + '|'.join(f"{h:>3d}" for h in range(24)))
fills = [f for f in tr['fills'] if day * 24 <= f[0] < day * 24 + 24 and f[2] in ('MILK', 'WOOL', 'STRAWBERRY', 'MELON')]
import collections
c = collections.defaultdict(lambda: [0, 0])
for t, sd, it, p in fills:
    c[(t, sd, it)][0] += 1; c[(t, sd, it)][1] += p
for k in sorted(c): print('fill', k[0] % 24, 'us' if k[1] == 0 else 'them', k[2], c[k][0], c[k][1])
