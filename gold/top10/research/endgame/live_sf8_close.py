"""sf8 (pinned from day 12) on the live191 games: close losses by group, product deltas (days 12-29)."""
import json, csv, collections
G = {int(r['episode_id']): r for r in csv.DictReader(open('replays/live_0926/analysis/games.csv', encoding='utf-8-sig'))}
def grp(r):
    g = r['opp_group']
    return 'copy' if g.startswith('copy (identical') else 'annex' if g.startswith('copy, we diverged') else 'left' if g.startswith('copy, left') else 'own'
by = collections.defaultdict(dict)
for l in open('gold/top10/gates/live_sf8_copyday.jsonl', encoding='utf-8'):
    r = json.loads(l); by[r['cand'].split('/')[-1]][r['gid']] = r
base = by['lean_sf8.py']; c22 = by['sf8_c22.py']
print('group  n  W(sf8) W(c22) | losses<1k 1-2k 2-3k 3-5k >5k (sf8)')
for g in ['copy','annex','left','own']:
    ids = [k for k in base if grp(G[k]) == g]
    hi = [k for k in ids if float(G[k]['opp_rating_before']) >= 2600]
    for nm, S in (('all', ids), ('2600+', hi)):
        ms = [base[k]['m'] for k in S]
        l = lambda a, b: sum(1 for m in ms if -b <= m < -a)
        print(f"{g:6s}{nm:6s} {len(S):3d} {sum(m>0 for m in ms):3d} {sum(c22[k]['m']>0 for k in S):3d} | {l(0,1000)} {l(1000,2000)} {l(2000,3000)} {l(3000,5000)} {l(5000,1e9)}")
print('\nsf8 losses within $3k: gid grp rating  m(sf8) m(c22) rec_m  lead24 lead29  top product deltas (us-them, d12-29)')
for k, r in sorted(base.items(), key=lambda kv: kv[1]['m']):
    if -3000 <= r['m'] < 0 or (-3000 <= c22[k]['m'] < 0):
        d = collections.Counter(r['led_us']); d.subtract(r['led_them'])
        top = sorted(d.items(), key=lambda kv: kv[1])[:4]
        print(k, grp(G[k]), G[k]['opp_rating_before'], int(r['m']), int(c22[k]['m']), int(r['rec']), G[k]['cash_lead_start_d24'], G[k]['cash_lead_start_d29'], ' '.join(f"{a[:5]}{int(b):+d}" for a, b in top))
