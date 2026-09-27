"""Split a closed-loop jsonl by strawberry-shop count k (first 4 shops) and by whether the candidate's rich takeover fired.
usage: cl_split.py file.jsonl [file2.jsonl ...]"""
import json, sys
S = ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET')
for f in sys.argv[1:]:
    rs = [json.loads(l) for l in open(f, encoding='utf-8')]
    grp = {}
    for r in rs:
        k = sum(x in S for x in (r.get('shops') or [])[:4])
        rich = (r.get('tel') or {}).get('gc_rich')
        key = ('k%d' % k if k >= 3 else 'k<3') + (' rich' if rich else '')
        g = grp.setdefault(key, [0, 0, 0, 0.0])
        g[0 if r['m'] > 0 else 1 if r['m'] < 0 else 2] += 1; g[3] += r['m']
    print(f, len(rs))
    for key in sorted(grp):
        w, l, d, m = grp[key]; n = w + l + d
        print('   %-10s %3d games  %3d-%3d-%3d  margin %+6d' % (key, n, w, l, d, m / n))
