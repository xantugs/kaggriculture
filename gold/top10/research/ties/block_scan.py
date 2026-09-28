"""Stationary blocks on shed-access tiles (tape_trace dumps, our side, days 6..19): a premium drop that could move to the
front of its block (right after the block's premium harvest, or at the block's start when the unit arrives carrying
premium). Reports the lead in steps, the lot, and whether the rival sold that product at the drop step.
usage: block_scan.py d_to trace.json [...]"""
import sys, json, collections
PREM = ('MILK', 'WOOL', 'STRAWBERRY')
MOV = ('NORTH', 'SOUTH', 'EAST', 'WEST')
ACC = {(4, 4), (5, 4), (4, 5), (5, 5)}
d_to = int(sys.argv[1])
tot = collections.Counter(); byk = collections.Counter()
for f in sys.argv[2:]:
    tr = json.load(open(f)); T = tr['tr']
    rs = collections.defaultdict(int)
    for t, sd, it, p in tr['fills']:
        if sd == 1: rs[(t, it)] += 1
    for day in range(6, d_to + 1):
        steps = [T.get(str(t)) for t in range(day * 24, day * 24 + 24)]
        nun = max(len(e[0]['cmd']) for e in steps if e)
        for u in range(nun):
            block = []
            def flush(block):
                if not block: return
                h0, pos0 = block[0][0], block[0][1]
                if tuple(pos0) not in ACC: return
                carried0 = any(block[0][3].get(k, 0) for k in PREM)
                e = 0 if carried0 else None
                for j, (h, pos, c, inv) in enumerate(block):
                    if c[0] == 'HARVEST':
                        nxt = steps[h + 1] if h + 1 < 24 else None
                        if nxt and u < len(nxt[0]['inv']) and any(nxt[0]['inv'][u].get(k, 0) > inv.get(k, 0) for k in PREM):
                            e = 1
                    prem_drop = (c[0] == 'PLACE' and c[1] in PREM) or (c[0] == 'DROP' and any(inv.get(k, 0) for k in PREM))
                    if prem_drop:
                        if e is None: e = j
                        lead = j - e
                        prod = c[1] if c[0] == 'PLACE' else '+'.join(k for k in PREM if inv.get(k, 0))
                        n = int(c[2]) if c[0] == 'PLACE' and len(c) > 2 else sum(inv.get(k, 0) for k in PREM)
                        t = day * 24 + h
                        tie = sum(rs[(t, k)] for k in PREM if inv.get(k, 0))
                        tot['drops'] += 1
                        if lead > 0:
                            tot['lead_drops'] += 1; tot['lead_steps'] += lead; byk[(prod, lead)] += 1
                            print(f"{tr['gid']} d{day} h{h:2d} u{u:2d} {prod:10s} n{n:3d} lead {lead} block {' '.join(b[2][0][:4] + ('/' + b[2][1][:2] if b[2][0] in ('PLACE', 'PICKUP') else '') for b in block)} rival_units_at_t {tie}")
                        return
            for h in range(24):
                e_ = steps[h]
                if not e_ or u >= len(e_[0]['cmd']) or u >= len(e_[0]['pos']):
                    flush(block); block = []; continue
                c = e_[0]['cmd'][u]; pos = e_[0]['pos'][u]; inv = e_[0]['inv'][u] if u < len(e_[0]['inv']) else {}
                if c[0] in MOV:
                    flush(block); block = []; continue
                if block and block[-1][1] != pos:
                    flush(block); block = []
                block.append((h, pos, c, inv))
            flush(block)
print(dict(tot)); print(sorted(byk.items()))
