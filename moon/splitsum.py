"""Summarize a pinned results file split by opponent class (gameclass.json: gid -> sim359). usage: splitsum.py results.jsonl [thr]"""
import sys, json, collections, statistics as st
import os
cls = json.load(open(os.environ.get('GCLASS', 'gameclass.json'))); thr = float(sys.argv[2]) if len(sys.argv) > 2 else 0.8
by = collections.defaultdict(dict)
for l in open(sys.argv[1], encoding='utf-8'):
    r = json.loads(l)
    if r['m'] is not None: by[r['gid']][r['label']] = r['m']
labs = sorted({k for d in by.values() for k in d}, key=lambda k: (k != 'base', k))
for name, test in (('MIRROR', lambda s: s >= thr), ('DIVERGENT', lambda s: s < thr)):
    g = [x for x in by if str(x) in cls and test(cls[str(x)]) and 'base' in by[x]]
    print(f"{name}: games {len(g)}")
    for lab in labs:
        gg = [x for x in g if lab in by[x]]
        if not gg: continue
        d = [by[x][lab] - by[x]['base'] for x in gg]; w = sum(by[x][lab] > 0 for x in gg)
        print(f"   {lab:16s} wins {w:3d}/{len(gg)}  margin {st.mean(by[x][lab] for x in gg):+8.0f}  vs base {st.mean(d):+7.0f} ± {st.pstdev(d) / len(d) ** .5:5.0f}")
