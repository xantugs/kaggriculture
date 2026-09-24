import json, collections, sys
fn = sys.argv[1]; base = sys.argv[2]
R=[json.loads(l) for l in open(fn)]
by=collections.defaultdict(dict)
for r in R: by[r['gid']][r['cand'].split('/')[-1]]=r
cands = sorted({r['cand'].split('/')[-1] for r in R} - {base})
for c in cands:
    d=[(v[c]['m']-v[base]['m'], v[base]['m'], v[c]['m']) for g,v in by.items() if c in v and base in v]
    if not d: continue
    n=len(d); mean=sum(x[0] for x in d)/n
    fw=sum(1 for x in d if x[1]<=0 and x[2]>0); fl=sum(1 for x in d if x[1]>0 and x[2]<=0)
    better=sum(1 for x in d if x[0]>0); worse=sum(1 for x in d if x[0]<0)
    srt=sorted(x[0] for x in d)
    print('%-16s n %3d mean %+6.0f median %+5.0f better/worse %3d/%3d flips +%d -%d' % (c, n, mean, srt[n//2], better, worse, fw, fl))
