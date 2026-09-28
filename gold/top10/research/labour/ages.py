"""Mean harvest age and units per harvest of one-time crops, per side, days d0-d1 (probe rows with k:/age:/hv: keys).
usage: ages.py rows.jsonl[,more] d0 d1"""
import sys, json, collections
rows = [json.loads(l) for p in sys.argv[1].split(',') for l in open(p, encoding='utf-8')]
d0, d1 = int(sys.argv[2]), int(sys.argv[3])
for side in ('days_us', 'days_elite'):
    a = collections.Counter()
    for r in rows:
        for d in range(d0, d1 + 1):
            c = r[side].get(str(d), {})
            for k, v in c.items():
                if k.startswith(('k:', 'age:', 'hv:', 'c:P:', 'e:')):
                    a[k] += v
    n = len(rows); nd = d1 - d0 + 1
    out = []
    for crop in ('WHEAT', 'CARROT'):
        h = a['k:HARV:' + crop]
        out.append(f"{crop}: harvests/day {h/n/nd:5.1f} mean age {a['age:'+crop]/max(1,h):.2f} units/harvest {a['hv:'+crop]/max(1,h):.2f}"
                   f" plants/day {a['k:PLAN:'+crop]/n/nd:5.1f} plots {a['c:P:'+crop]/n/nd:5.1f} fert/day {a['k:FERT:'+crop]/n/nd:4.1f}")
    print(side, ' | '.join(out))
