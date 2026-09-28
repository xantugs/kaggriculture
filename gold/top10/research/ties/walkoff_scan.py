"""Access-tile blocks (our side, days 6..d_to) where the unit holds premium goods (carried in or harvested there) and
walks off without dropping them; reports the block, whether it holds a PASS (a free turn for a PLACE), and the step of
that unit's next premium drop. usage: walkoff_scan.py d_to trace.json [...]"""
import sys, json, collections
PREM = ('MILK', 'WOOL', 'STRAWBERRY', 'MELON')
MOV = ('NORTH', 'SOUTH', 'EAST', 'WEST')
ACC = {(4, 4), (5, 4), (4, 5), (5, 5)}
d_to = int(sys.argv[1]); tot = collections.Counter()
for f in sys.argv[2:]:
    tr = json.load(open(f)); T = tr['tr']
    for day in range(6, d_to + 1):
        steps = [T.get(str(t)) for t in range(day * 24, day * 24 + 24)]
        nun = max(len(e[0]['cmd']) for e in steps if e)
        for u in range(nun):
            h = 0
            while h < 24:
                e_ = steps[h]
                if not e_ or u >= len(e_[0]['cmd']) or u >= len(e_[0]['pos']) or tuple(e_[0]['pos'][u]) not in ACC or e_[0]['cmd'][u][0] in MOV:
                    h += 1; continue
                pos = tuple(e_[0]['pos'][u]); blk = []
                while h < 24 and steps[h] and u < len(steps[h][0]['cmd']) and tuple(steps[h][0]['pos'][u]) == pos and steps[h][0]['cmd'][u][0] not in MOV:
                    blk.append((h, steps[h][0]['cmd'][u], steps[h][0]['inv'][u] if u < len(steps[h][0]['inv']) else {})); h += 1
                if h >= 24: continue
                # inventory when it walks off
                inv_off = steps[h][0]['inv'][u] if steps[h] and u < len(steps[h][0]['inv']) else {}
                prem = {k: inv_off[k] for k in PREM if inv_off.get(k, 0)}
                if not prem: continue
                has_pass = any(c[0] == 'PASS' for _, c, _ in blk)
                # next drop
                nd = None
                for h2 in range(h, 24):
                    c = steps[h2][0]['cmd'][u] if steps[h2] and u < len(steps[h2][0]['cmd']) else ['PASS']
                    if c[0] == 'DROP' or (c[0] == 'PLACE' and c[1] in PREM): nd = h2; break
                tot['n'] += 1; tot['units'] += sum(prem.values()); tot['pass'] += has_pass
                print(f"{tr['gid']} d{day} u{u:2d} h{blk[0][0]:2d}-{h-1:2d} {' '.join(c[0][:4] + ('/' + c[1][:2] if c[0] in ('PLACE', 'PICKUP') else '') for _, c, _ in blk)} -> carries {prem} next drop h{nd} pass {has_pass}")
print(dict(tot))
