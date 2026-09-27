"""Margin distribution and cash lead at d24/d29 in the 191 live games (games.csv)."""
import csv, sys, statistics as st
rows = list(csv.DictReader(open('replays/live_0926/analysis/games.csv', encoding='utf-8-sig')))
def f(x):
    try: return float(x)
    except: return None
print(len(rows), 'games')
from collections import Counter, defaultdict
print(Counter(r['opp_group'] for r in rows))
print(Counter(r['opp_type'] for r in rows))
bins = [(-1e9,-10000),(-10000,-5000),(-5000,-3000),(-3000,-2000),(-2000,-1000),(-1000,0),(0,1000),(1000,2000),(2000,3000),(3000,5000),(5000,10000),(10000,1e9)]
def binname(b): return f"[{b[0]/1000:.0f}k,{b[1]/1000:.0f}k)"
for grp in ['all','copy','own']:
    sel = [r for r in rows if grp=='all' or (grp=='copy' and r['opp_group'].startswith(('identical','copy','on the'))) or (grp=='own' and not r['opp_group'].startswith(('identical','copy','on the')))]
    print('\n==', grp, len(sel))
    for hi in [False, True]:
        s2 = [r for r in sel if (f(r['opp_rating_before']) or 0) >= 2600] if hi else sel
        c = Counter()
        for r in s2:
            m = f(r['margin'])
            for b in bins:
                if b[0] <= m < b[1]: c[binname(b)] += 1
        print(' 2600+' if hi else ' all', len(s2), ' '.join(f"{binname(b)}:{c[binname(b)]}" for b in bins))
