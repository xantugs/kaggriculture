"""Idle tails (tape_trace dumps, our side, days 6..d_to): a unit whose commands are PASS from hour h to the end of the day
while it carries premium goods; can it reach a shed-access tile and drop by hour 23? Also mid-day PASS blocks long enough
for a round trip. usage: idle_scan.py d_to trace.json [...]"""
import sys, json, collections
PREM = ('MILK', 'WOOL', 'STRAWBERRY', 'MELON')
ACC = [(4, 4), (5, 4), (4, 5), (5, 5)]
d_to = int(sys.argv[1])
tot = collections.Counter()
for f in sys.argv[2:]:
    tr = json.load(open(f)); T = tr['tr']
    for day in range(6, d_to + 1):
        steps = [T.get(str(t)) for t in range(day * 24, day * 24 + 24)]
        nun = max(len(e[0]['cmd']) for e in steps if e)
        for u in range(nun):
            h = 23
            while h >= 0 and steps[h] and u < len(steps[h][0]['cmd']) and steps[h][0]['cmd'][u][0] == 'PASS':
                h -= 1
            h += 1   # first hour of the idle tail
            if h > 23 or not steps[h] or u >= len(steps[h][0]['inv']):
                continue
            inv = steps[h][0]['inv'][u]; pos = steps[h][0]['pos'][u]
            car = {k: inv[k] for k in PREM if inv.get(k, 0)}
            if not car: continue
            d = min(abs(pos[0] - a) + abs(pos[1] - b) for a, b in ACC)
            ok = h + d <= 23
            tot['tails'] += 1; tot['units'] += sum(car.values())
            if ok: tot['ok'] += 1; tot['ok_units'] += sum(car.values())
            print(f"{tr['gid']} d{day} u{u:2d} idle from h{h:2d} dist {d} carry {car} {'OK' if ok else '--'}")
print(dict(tot))
