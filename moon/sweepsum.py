import json, sys, collections, statistics as st
import os
cls = json.load(open(os.environ.get('GCLASS', 'gameclass.json')))
by = collections.defaultdict(dict)
for l in open(sys.argv[1], encoding='utf-8'):
    r = json.loads(l)
    if r['m'] is not None: by[r['gid']][r['label']] = r['m']
labs = sorted({k for d in by.values() for k in d})
rows = []
for lab in labs:
    out = {}
    for name, test in (('MIR', lambda s: s >= 0.8), ('DIV', lambda s: s < 0.8)):
        g = [x for x in by if test(cls.get(str(x), 0)) and 'base' in by[x] and lab in by[x]]
        dd = [by[x][lab] - by[x]['base'] for x in g]
        out[name] = (st.mean(dd), st.pstdev(dd) / len(dd) ** .5, sum(by[x][lab] > 0 for x in g) - sum(by[x]['base'] > 0 for x in g), len(g))
    rows.append((lab, out))
rows.sort(key=lambda r: -(r[1]['MIR'][0] * 71 + r[1]['DIV'][0] * 60) / 131)
for lab, o in rows[:int(sys.argv[2]) if len(sys.argv) > 2 else 25]:
    m, d = o['MIR'], o['DIV']
    print(f"{lab:40s} MIR {m[0]:+6.0f} ±{m[1]:4.0f} dW {m[2]:+3d} | DIV {d[0]:+6.0f} ±{d[1]:4.0f} dW {d[2]:+3d} | all {(m[0]*m[3]+d[0]*d[3])/(m[3]+d[3]):+6.0f}")
