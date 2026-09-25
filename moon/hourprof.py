import json, sys, collections
o = json.load(open(sys.argv[1])); item = sys.argv[2]; D0, D1 = int(sys.argv[3]), int(sys.argv[4])
g = len(o)
u = [collections.Counter(), collections.Counter()]; r = [collections.Counter(), collections.Counter()]
lots = [collections.Counter(), collections.Counter()]
for gid, x in o.items():
    per = collections.Counter()
    for s, it, p, w, held, tot in x['sales']:
        if it == item and D0*24 <= s < (D1+1)*24:
            u[w][s % 24] += 1; r[w][s % 24] += p; per[(w, s)] += 1
    for (w, s), n in per.items():
        lots[w][min(n, 30)//5*5] += 1
print(item, f'days {D0}-{D1}: per hour units us/them @ price')
for h in range(24):
    if u[0][h] or u[1][h]:
        print(f'  h{h:02d} us {u[0][h]/g:5.2f} @ {r[0][h]/max(1,u[0][h]):5.0f}   them {u[1][h]/g:5.2f} @ {r[1][h]/max(1,u[1][h]):5.0f}')
print('  lot sizes (bucket of 5): us', sorted(lots[0].items()), ' them', sorted(lots[1].items()))
