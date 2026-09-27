"""Expected net wins per 100 games for a per-game gain ~ N(mu, sd) added to sf8's margins, per population."""
import json, csv, math, collections
Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
def rows(p, cand=None, key='m'):
    out = {}
    for l in open(p, encoding='utf-8'):
        r = json.loads(l)
        if cand and r.get('cand') != cand: continue
        out[(r['gid'], r.get('seat'))] = r
    return list(out.values())
G = {int(r['episode_id']): r for r in csv.DictReader(open('replays/live_0926/analysis/games.csv', encoding='utf-8-sig'))}
live = rows('gold/top10/gates/live_sf8_copyday.jsonl', 'gold/top10/lean_sf8.py')
def lg(r):
    g = G[r['gid']]['opp_group']; return 'copy' if g.startswith('copy (identical') else ('own' if g.startswith(('own',)) else 'other')
pops = {
    'goldg (111)': [r['m'] for r in rows('gold/top10/gates/goldg_sf8.jsonl')],
    'top10g (270)': [r['m'] for r in rows('gold/top10/gates/top10g_sf8.jsonl')],
    'live copy (105)': [r['m'] for r in live if lg(r) == 'copy'],
    'live own (54)': [r['m'] for r in live if lg(r) == 'own'],
    'live 2600+ (46)': [r['m'] for r in live if float(G[r['gid']]['opp_rating_before']) >= 2600],
    's2800 (149)': [r['m'] for r in rows('gold/top10/gates/s2800_sf8.jsonl', 'gold/top10/lean_sf8.py')],
}
print('population        n  wins |  net wins per 100 games for mean gain (sd = max(700, 0.8*mean))')
print('                            |   +250    +500   +1000   +2000   +3000   +4000')
for k, ms in pops.items():
    w = sum(m > 0 for m in ms)
    out = []
    for mu in (250, 500, 1000, 2000, 3000, 4000):
        sd = max(700, 0.8 * mu)
        exp_w = sum(Phi((m + mu) / sd) for m in ms)
        out.append(100 * (exp_w - w) / len(ms))
    print(f"{k:18s} {len(ms):3d} {w:4d} | " + ' '.join(f"{x:+7.1f}" for x in out))
