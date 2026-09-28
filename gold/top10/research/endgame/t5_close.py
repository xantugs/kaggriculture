"""T5 vs sf8 on live191 (and pin249 where available): margin distribution by group, close losses and product deltas.
usage: t5_close.py"""
import json, csv, collections
G = {int(r['episode_id']): r for r in csv.DictReader(open('replays/live_0926/analysis/games.csv', encoding='utf-8-sig'))}
def grp(g):
    g = G[g]['opp_group']
    return 'copy' if g.startswith('copy (identical') else 'annex' if g.startswith('copy, we diverged') else 'left' if g.startswith('copy, left') else 'own'
def load(p, cand=None):
    d = {}
    for l in open(p, encoding='utf-8'):
        r = json.loads(l)
        if cand and r.get('cand') != cand: continue
        d[r['gid']] = r
    return d
sf8 = load('gold/top10/gates/live_sf8_copyday.jsonl', 'gold/top10/lean_sf8.py')
t5 = load('gold/top10/gates/live_T5.jsonl')
bins = [-1e9, -5000, -3000, -2000, -1000, 0, 1000, 2000, 3000, 5000, 1e9]
def hist(ms):
    c = [0] * (len(bins) - 1)
    for m in ms:
        for i in range(len(bins) - 1):
            if bins[i] <= m < bins[i + 1]: c[i] += 1
    return ' '.join(f"{c[i]:3d}" for i in range(len(c)))
print('bins:', ' '.join(f"{int(b/1000) if abs(b)<1e8 else 'inf'}k" for b in bins))
for nm, D in (('sf8', sf8), ('T5', t5)):
    for g in ('copy', 'annex', 'own', 'left', 'ALL'):
        for hi in (0, 1):
            ks = [k for k in D if (g == 'ALL' or grp(k) == g) and (not hi or float(G[k]['opp_rating_before']) >= 2600)]
            if not ks: continue
            ms = [D[k]['m'] for k in ks]
            print(f"{nm:4s} {g:5s} {'2600+' if hi else 'all  '} n={len(ks):3d} W={sum(m > 0 for m in ms):3d} | {hist(ms)}")
print('\nT5 losses (and sf8 margin): gid grp rating m_T5 m_sf8 lead24 lead29 | product deltas us-them d12-29 (T5)')
for k, r in sorted(t5.items(), key=lambda kv: kv[1]['m']):
    if r['m'] < 0 or sf8[k]['m'] < 0 and sf8[k]['m'] > -3000:
        d = collections.Counter(r['led_us']); d.subtract(r['led_them'])
        top = sorted(d.items(), key=lambda kv: kv[1])[:4]
        print(k, f"{grp(k):5s}", G[k]['opp'] if 'opp' in G[k] else G[k]['opponent'][:14].ljust(14), G[k]['opp_rating_before'], f"{int(r['m']):+7d} {int(sf8[k]['m']):+7d}", G[k]['cash_lead_start_d24'], G[k]['cash_lead_start_d29'], ' '.join(f"{a[:5]}{int(b):+d}" for a, b in top))
