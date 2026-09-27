"""Margin distribution of sf8 on goldg/top10g/pin249/live191/s2800 rows."""
import json, sys
from collections import Counter, defaultdict
bins = [-1e9,-10000,-5000,-3000,-2000,-1000,0,1000,2000,3000,5000,1e9]
def hist(ms):
    c=[0]*(len(bins)-1)
    for m in ms:
        for i in range(len(bins)-1):
            if bins[i]<=m<bins[i+1]: c[i]+=1
    return ' '.join(f"{int(bins[i]/1000) if abs(bins[i])<1e8 else '-inf'}k:{c[i]}" for i in range(len(c)))
def load(p, cand=None):
    out={}
    for l in open(p,encoding='utf-8'):
        r=json.loads(l)
        if cand and r.get('cand')!=cand: continue
        k=(r['gid'],r.get('seat'))
        out[k]=r
    return list(out.values())
for p,c in [('gold/top10/gates/goldg_sf8.jsonl',None),('gold/top10/gates/top10g_sf8.jsonl',None),('gold/top10/gates/live_sf8_copyday.jsonl','gold/top10/lean_sf8.py'),('gold/top10/gates/pin249_sf8.jsonl',None),('gold/top10/gates/s2800_sf8.jsonl',None)]:
    rs=load(p,c)
    cands=Counter(r.get('cand') for r in rs)
    ms=[r['m'] for r in rs]
    print(p, len(rs), dict(cands) if len(cands)<4 else len(cands), 'wins',sum(m>0 for m in ms))
    print('  ',hist(ms))
    if 'team' in rs[0]:
        by=defaultdict(list)
        for r in rs: by[r['team']].append(r['m'])
        for t,v in by.items():
            print('   ',t[:20].ljust(20), len(v), 'W',sum(x>0 for x in v), 'within2k L',sum(-2000<=x<0 for x in v),'W',sum(0<x<2000 for x in v), ' L>5k', sum(x<-5000 for x in v))
