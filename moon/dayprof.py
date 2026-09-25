import json, sys, collections
o = json.load(open(sys.argv[1])); items = sys.argv[2].split(',')
g = len(o)
for item in items:
    print(item, 'per day: units us/them @ avg price us/them')
    u = [collections.Counter(), collections.Counter()]; r = [collections.Counter(), collections.Counter()]
    for gid, x in o.items():
        for s, it, p, w, held, tot in x['sales']:
            if it == item: u[w][s // 24] += 1; r[w][s // 24] += p
    for d in range(4, 30):
        if u[0][d] or u[1][d]:
            print(f'  d{d:02d} us {u[0][d]/g:5.1f} @ {r[0][d]/max(1,u[0][d]):5.0f}   them {u[1][d]/g:5.1f} @ {r[1][d]/max(1,u[1][d]):5.0f}')
