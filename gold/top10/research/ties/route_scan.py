"""Premium drop segments that hold only moves and premium harvests (days 6..d_to, our side): the tape's segment length
vs the shortest walk from the segment start through the same harvest tiles to a shed-access tile (+ harvests + drop).
Slack = turns a re-routed harvest round would deliver early. usage: route_scan.py d_to trace.json [...]"""
import sys, json, collections, itertools
PREM = ('MILK', 'WOOL', 'STRAWBERRY', 'MELON')
MOV = ('NORTH', 'SOUTH', 'EAST', 'WEST')
ACC = [(4, 4), (5, 4), (4, 5), (5, 5)]
def d(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
d_to = int(sys.argv[1]); tot = collections.Counter(); hist = collections.Counter()
for f in sys.argv[2:]:
    tr = json.load(open(f)); T = tr['tr']
    for day in range(6, d_to + 1):
        steps = [T.get(str(t)) for t in range(day * 24, day * 24 + 24)]
        nun = max(len(e[0]['cmd']) for e in steps if e)
        for u in range(nun):
            seg = []
            for h in range(24):
                e = steps[h]
                if not e or u >= len(e[0]['cmd']) or u >= len(e[0]['pos']): continue
                c = e[0]['cmd'][u]; inv = e[0]['inv'][u] if u < len(e[0]['inv']) else {}; pos = tuple(e[0]['pos'][u])
                if c[0] in ('PLACE', 'DROP', 'PICKUP') or c[0] not in MOV + ('HARVEST',):
                    prem = (c[0] == 'DROP' and any(inv.get(k, 0) for k in PREM)) or (c[0] == 'PLACE' and c[1] in PREM)
                    if prem and seg and all(x[1] in MOV or x[1] == 'HARVEST' for x in seg):
                        hv = [x[2] for x in seg if x[1] == 'HARVEST']
                        if len(hv) >= 2 and len(hv) <= 7:
                            start = seg[0][2]
                            best = min(sum(d(a, b) for a, b in zip((start,) + p, p)) + min(d(p[-1], a) for a in ACC) for p in itertools.permutations(hv))
                            opt = best + len(hv) + 1
                            tape = len(seg) + 1
                            slack = tape - opt
                            tot['n'] += 1; tot['slack'] += slack; hist[slack] += 1
                            if slack > 0:
                                prod = c[1] if c[0] == 'PLACE' else '+'.join(x for x in PREM if inv.get(x, 0))
                                print(f"{tr['gid']} d{day} h{h:2d} u{u:2d} {prod:10s} harv{len(hv)} tape{tape} opt{opt} slack{slack}")
                    seg = []
                    continue
                seg.append((h, c[0], pos))
print(dict(tot), sorted(hist.items()))
