"""Cash lead at start of d24 / d29 vs final margin in the 191 live games."""
import csv, statistics as st
from collections import Counter
rows = list(csv.DictReader(open('replays/live_0926/analysis/games.csv', encoding='utf-8-sig')))
f = lambda x: float(x) if x not in ('', None) else None
def grp(r):
    g = r['opp_group']
    if g.startswith('copy (identical'): return 'copy'
    if g.startswith('copy, we diverged'): return 'annex'
    if g.startswith('copy, left'): return 'left'
    return 'own'
for G in ['copy','annex','own','ALL']:
    sel = [r for r in rows if G=='ALL' or grp(r)==G]
    for hi in (0,1):
        s = [r for r in sel if not hi or f(r['opp_rating_before'])>=2600]
        if not s: continue
        d24 = [f(r['cash_lead_start_d24']) for r in s]; d29=[f(r['cash_lead_start_d29']) for r in s]; m=[f(r['margin']) for r in s]
        late = [mm-a for mm,a in zip(m,d24)]   # days 24-29 swing
        last = [mm-b for mm,b in zip(m,d29)]   # day 29 swing
        mid = [b-a for a,b in zip(d24,d29)]    # days 24-28 swing
        W = sum(x>0 for x in m)
        led29_lost = sum(1 for a,x in zip(d29,m) if a>0 and x<0)
        led24_lost = sum(1 for a,x in zip(d24,m) if a>0 and x<0)
        trail29_won = sum(1 for a,x in zip(d29,m) if a<0 and x>0)
        trail24_won = sum(1 for a,x in zip(d24,m) if a<0 and x>0)
        print(f"{G:5s} {'2600+' if hi else 'all  '} n={len(s):3d} W={W:3d} | d24->end swing med {st.median(late):+7.0f} mean {st.mean(late):+7.0f} | d24-28 med {st.median(mid):+7.0f} | d29 swing med {st.median(last):+7.0f} mean {st.mean(last):+7.0f} | led@24 lost {led24_lost} trail@24 won {trail24_won} | led@29 lost {led29_lost} trail@29 won {trail29_won}")
print()
print('Losses within $3k (all groups): gid, grp, rating, lead24, lead29, margin')
for r in sorted(rows, key=lambda r: f(r['margin'])):
    m=f(r['margin'])
    if -5000 <= m < 0:
        print(r['episode_id'], r['version'], grp(r), r['opponent'][:18], r['opp_rating_before'], r['cash_lead_start_d24'], r['cash_lead_start_d29'], int(m))
print('\nWins within $2k:')
for r in sorted(rows, key=lambda r: f(r['margin'])):
    m=f(r['margin'])
    if 0 < m < 2000:
        print(r['episode_id'], r['version'], grp(r), r['opponent'][:18], r['opp_rating_before'], r['cash_lead_start_d24'], r['cash_lead_start_d29'], int(m))
