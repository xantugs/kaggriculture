"""Scan premium drops of our units on days 6-21 in a tape_trace dump: for each drop (PLACE/DROP of MILK/WOOL/STRAWBERRY)
the load, the unit's segment since its last shed visit, the non-move non-premium commands in it (deferrable), the
earliest drop step if they were skipped, the idle (PASS) steps left after the drop that day, and whether the copy
dropped the same product at the same step. usage: drop_scan.py trace.json [...]"""
import sys, json, collections
PREM = ('MILK', 'WOOL', 'STRAWBERRY')
MOV = ('NORTH', 'SOUTH', 'EAST', 'WEST')
tot = collections.Counter()
for f in sys.argv[1:]:
    tr = json.load(open(f)); T = tr['tr']
    for day in range(6, 22):
        for side in (0,):
            steps = [T.get(str(t)) for t in range(day * 24, day * 24 + 24)]
            nun = max(len(e[side]['cmd']) for e in steps if e)
            for u in range(nun):
                seg = []
                for h in range(24):
                    t = day * 24 + h
                    e = steps[h]
                    if not e or u >= len(e[side]['cmd']) or u >= len(e[side]['inv']):
                        continue
                    c = e[side]['cmd'][u]; inv = e[side]['inv'][u]
                    carried = {k: inv.get(k, 0) for k in PREM if inv.get(k, 0)}
                    if c[0] in ('PLACE', 'DROP', 'PICKUP') :
                        prem = c[0] == 'DROP' and carried or (c[0] == 'PLACE' and c[1] in PREM)
                        if prem:
                            n = sum(carried.values()) if c[0] == 'DROP' else int(c[2]) if len(c) > 2 else 1
                            defer = [s for s in seg if s[1] not in MOV and not (s[1] == 'HARVEST' and s[2]) and s[1] != 'PASS']
                            harv = [s for s in seg if s[1] == 'HARVEST' and s[2]]
                            idle = sum(1 for h2 in range(h + 1, 24) if steps[h2] and u < len(steps[h2][side]['cmd']) and steps[h2][side]['cmd'][u][0] == 'PASS')
                            prod = c[1] if c[0] == 'PLACE' else '+'.join(sorted(carried))
                            tot['drops'] += 1; tot['units'] += n
                            tot['defer_steps'] += len(defer); tot['defer_units_x_steps'] += n * len(defer)
                            tot['n_defer>0'] += bool(defer)
                            print(f"{tr['gid']} d{day} h{h:2d} u{u:2d} {prod:10s} n{n:3d} seg{len(seg):3d} harv{len(harv)} defer {len(defer)} [{' '.join(s[1][:4] for s in defer)}] idle_after {idle}")
                        seg = []
                        continue
                    # premium harvest? (next step's inv grows)
                    nxt = steps[h + 1] if h + 1 < 24 else None
                    ph = False
                    if c[0] == 'HARVEST' and nxt and u < len(nxt[side]['inv']):
                        ni = nxt[side]['inv'][u]
                        ph = any(ni.get(k, 0) > inv.get(k, 0) for k in PREM)
                    seg.append((h, c[0], ph))
print(dict(tot))
