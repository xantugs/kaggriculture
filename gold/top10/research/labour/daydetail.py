"""Per-day mean action mix for us vs elite over a day range (gate probe output)."""
import sys, json, collections
paths = sys.argv[1].split(','); d0, d1 = int(sys.argv[2]), int(sys.argv[3])
rows = [json.loads(l) for p in paths for l in open(p, encoding='utf-8')]
keys = ['hire', 'wage', 'ut', 'mv', 'pass', 'e:PLANT', 'e:WATER', 'wy', 'wm', 'e:HARVEST', 'e:FEED', 'e:CARE', 'e:COLLECT_FERTILIZER', 'e:FERTILIZE', 'e:DIG', 'e:DROP', 'e:PICKUP', 'e:PLACE']
short = ['hire', 'wage', 'ut', 'mv', 'pass', 'plant', 'water', 'wy', 'wm', 'harv', 'feed', 'care', 'coll', 'fert', 'dig', 'drop', 'pick', 'place']
print(len(rows), 'seats')
print('day side ' + ''.join(f'{s:>7s}' for s in short) + '  hv:W   C   T   S   E   M  Wo  pW  pC  pT  pS')
for d in range(d0, d1 + 1):
    for side in ('days_us', 'days_elite'):
        a = collections.Counter()
        for r in rows:
            c = r[side].get(str(d), {})
            for k, v in c.items():
                a[k] += v
        n = len(rows)
        line = f'{d:3d} {side[5:7]:4s} ' + ''.join(f'{a[k]/n:7.1f}' for k in keys)
        line += ' ' + ''.join(f"{a['hv:'+p]/n:4.0f}" for p in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'EGG', 'MILK', 'WOOL'))
        line += ''.join(f"{a['c:P:'+p]/n:4.0f}" for p in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY'))
        print(line)
