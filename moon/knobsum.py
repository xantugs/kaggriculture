import json, sys, collections, statistics as st
by = collections.defaultdict(dict)
for l in open(sys.argv[1], encoding='utf-8'):
    r = json.loads(l)
    if r['m'] is not None: by[r['gid']][r['label']] = r['m']
labs = sorted({k for d in by.values() for k in d})
pat = sys.argv[2] if len(sys.argv) > 2 else ''
for lab in labs:
    if pat and pat not in lab: continue
    g = [x for x in by if 'base' in by[x] and lab in by[x]]
    dd = [by[x][lab] - by[x]['base'] for x in g]
    print(f"{lab:40s} n {len(g)} d {st.mean(dd):+7.0f} ± {st.pstdev(dd)/len(dd)**.5:4.0f} dW {sum(by[x][lab]>0 for x in g)-sum(by[x]['base']>0 for x in g):+d}")
