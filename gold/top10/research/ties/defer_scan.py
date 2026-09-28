"""Deferral with idle recovery (tape_trace dumps, our side, days 6..d_to): premium drops whose segment since the unit's
last shed visit holds COLLECT_FERTILIZER commands (k of them). Skipping them drops the lot k turns earlier; the skipped
collections are then done in the unit's first PASS block after the drop: feasible when the block (+ the k turns gained)
covers the walk from the block's tile to the collection tiles and back (no return needed when the block ends the day).
Reports feasibility, the lead, the tick window of the new drop turn vs the old, the rival's units sold at the old turn.
usage: defer_scan.py d_to trace.json [...]"""
import sys, json, collections
PREM = ('MILK', 'WOOL', 'STRAWBERRY', 'MELON')
MOV = ('NORTH', 'SOUTH', 'EAST', 'WEST')
d_to = int(sys.argv[1]); tot = collections.Counter()
def dist(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])
def tour(start, pts, back):
    import itertools
    best = 10 ** 9
    for perm in itertools.permutations(pts):
        p = start; c = 0
        for q in perm: c += dist(p, q); p = q
        if back: c += dist(p, start)
        best = min(best, c)
    return best
for f in sys.argv[2:]:
    tr = json.load(open(f)); T = tr['tr']
    rs = collections.Counter()
    for t, sd, it, p in tr['fills']:
        if sd == 1: rs[(t, it)] += 1
    for day in range(6, d_to + 1):
        steps = [T.get(str(t)) for t in range(day * 24, day * 24 + 24)]
        nun = max(len(e[0]['cmd']) for e in steps if e)
        for u in range(nun):
            seg = []
            for h in range(24):
                e = steps[h]
                if not e or u >= len(e[0]['cmd']) or u >= len(e[0]['pos']): continue
                c = e[0]['cmd'][u]; inv = e[0]['inv'][u] if u < len(e[0]['inv']) else {}; pos = tuple(e[0]['pos'][u])
                if c[0] in ('PLACE', 'DROP', 'PICKUP'):
                    prem = (c[0] == 'DROP' and any(inv.get(k, 0) for k in PREM)) or (c[0] == 'PLACE' and c[1] in PREM)
                    if prem:
                        xs = [(hh, p) for hh, cc, p in seg if cc == 'COLLECT_FERTILIZER']
                        if xs:
                            k = len(xs)
                            # first PASS block after the drop
                            a = None
                            for h2 in range(h + 1, 24):
                                c2 = steps[h2][0]['cmd'][u] if steps[h2] and u < len(steps[h2][0]['cmd']) else ['PASS']
                                if c2[0] == 'PASS':
                                    a = h2; break
                            feas = False; need = None; L = 0; q = None
                            if a is not None:
                                b = a
                                while b + 1 < 24 and steps[b + 1] and u < len(steps[b + 1][0]['cmd']) and steps[b + 1][0]['cmd'][u][0] == 'PASS': b += 1
                                q = tuple(steps[a][0]['pos'][u]); L = b - a + 1
                                back = b < 23
                                need = tour(q, [p for _, p in xs], back) + k
                                feas = need <= L + k
                            prod = c[1] if c[0] == 'PLACE' else '+'.join(x for x in PREM if inv.get(x, 0))
                            t_d = day * 24 + h; t_e = t_d - k
                            same = (t_e - 1) // 4 == (t_d - 1) // 4
                            riv = sum(rs[(t_d, x)] for x in PREM)
                            tot['events'] += 1; tot['feas'] += feas; tot['feas_same'] += feas and same
                            print(f"{tr['gid']} d{day} h{h:2d} u{u:2d} {prod:10s} k{k} idle@{a} len{L} need{need} {'FEAS' if feas else '--'} {'same' if same else 'cross'} rival{riv}")
                    seg = []
                    continue
                seg.append((h, c[0], pos))
print(dict(tot))
