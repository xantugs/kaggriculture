import json, sys, collections
o = json.load(open(sys.argv[1])); item = sys.argv[2]; D0, D1 = int(sys.argv[3]), int(sys.argv[4])
g = len(o)
for who in (0, 1):
    b = collections.Counter(); r = collections.Counter()
    for gid, x in o.items():
        for s, it, p, w, held, tot in x['sales']:
            if w == who and it == item and D0*24 <= s < (D1+1)*24:
                k = '<=1' if p <= 1 else '<20' if p < 20 else '<60' if p < 60 else '<100' if p < 100 else '<140' if p < 140 else '140+'
                b[k] += 1; r[k] += p
    print('us' if who == 0 else 'them', {k: (round(b[k]/g, 1), round(r[k]/max(1,b[k]))) for k in ['<=1','<20','<60','<100','<140','140+']})
# per game: our cheap count vs margin
rows = []
for gid, x in o.items():
    c = [0, 0]
    for s, it, p, w, held, tot in x['sales']:
        if it == item and p < 20 and D0*24 <= s < (D1+1)*24: c[w] += 1
    rows.append((c[0], c[1], x['m'], gid))
rows.sort(reverse=True)
print('games with most cheap(<20) sales us/them/margin:', rows[:15])
print('games with any cheap us:', sum(r[0] > 0 for r in rows), 'them:', sum(r[1] > 0 for r in rows))
