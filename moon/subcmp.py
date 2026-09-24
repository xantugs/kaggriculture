"""Compare our submissions' ladder records by opponent rating band and common opponents. usage: subcmp.py eps.json sub1,sub2,..."""
import sys, json, collections
eps = json.load(open(sys.argv[1], encoding='utf-8')); subs = [int(x) for x in sys.argv[2].split(',')]
bands = [(0, 2600), (2600, 2700), (2700, 2800), (2800, 2900), (2900, 9999)]
res = {s: collections.defaultdict(lambda: [0, 0, []]) for s in subs}
opp = {s: collections.defaultdict(lambda: [0, 0]) for s in subs}
first = {}
for e in eps:
    for k, sb in enumerate(e['sub']):
        if sb in subs and e['teams'][k] == 'offhand' and None not in e['r']:
            o = 1 - k; m = e['r'][k] - e['r'][o]; sc = e['score'][o] or 0
            b = next(b for b in bands if b[0] <= sc < b[1])
            r = res[sb][b]; r[0 if m > 0 else 1] += 1; r[2].append(m)
            q = opp[sb][e['teams'][o]]; q[0 if m > 0 else 1] += 1
            first.setdefault(sb, []).append((e['t'], m, sc, e['score'][k]))
for sb in subs:
    rows = sorted(first.get(sb, []))
    tot = sum(r[0] for r in res[sb].values()), sum(r[1] for r in res[sb].values())
    print(f"sub {sb}: games {len(rows)}  W {tot[0]} L {tot[1]}  own rating first/last {rows[0][3] if rows else None} -> {rows[-1][3] if rows else None}")
    for b in bands:
        w, l, ms = res[sb][b]
        if w + l: print(f"   opp {b[0]}-{b[1]}: W{w:3d} L{l:3d} ({100*w/(w+l):3.0f}%)  mean margin {sum(ms)/len(ms):+7.0f}")
