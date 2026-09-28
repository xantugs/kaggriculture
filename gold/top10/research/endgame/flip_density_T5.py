"""Expected net wins per 100 games for a per-game gain ~ N(mu, sd) added to T5's margins (and a pure shift), per population.
usage: flip_density_T5.py goldg_T5_daylog.jsonl"""
import json, csv, math, sys
Phi = lambda z: 0.5 * (1 + math.erf(z / math.sqrt(2)))
G = {int(r['episode_id']): r for r in csv.DictReader(open('replays/live_0926/analysis/games.csv', encoding='utf-8-sig'))}
def rows(p):
    out = {}
    for l in open(p, encoding='utf-8'):
        r = json.loads(l); out[(r['gid'], r.get('seat'))] = r
    return list(out.values())
live = rows('gold/top10/gates/live_T5.jsonl')
grp = lambda r: 'copy' if G[r['gid']]['opp_group'].startswith('copy (identical') else ('own' if G[r['gid']]['opp_group'].startswith('own') else 'other')
pops = {
    'goldg T5 (111)': [r['m'] for r in rows(sys.argv[1])],
    'pin249 T5': [r['m'] for r in rows('gold/top10/gates/pin249_T5.jsonl')],
    'live T5 copy': [r['m'] for r in live if grp(r) == 'copy'],
    'live T5 own': [r['m'] for r in live if grp(r) == 'own'],
    'live T5 2600+': [r['m'] for r in live if float(G[r['gid']]['opp_rating_before']) >= 2600],
}
print('population          n  wins | L<1k L1-2k W<1k W1-2k |  net wins/100 for mean gain, sd=max(700,0.8mu) [pure shift]')
print('                                                     |      +250          +500         +1000         +2000')
for k, ms in pops.items():
    w = sum(m > 0 for m in ms); n = len(ms)
    out = []
    for mu in (250, 500, 1000, 2000):
        sd = max(700, 0.8 * mu)
        exp_w = sum(Phi((m + mu) / sd) for m in ms)
        shift = sum(1 for m in ms if -mu < m <= 0)
        out.append(f"{100 * (exp_w - w) / n:+5.1f} [{100 * shift / n:4.1f}]")
    c = lambda a, b: sum(1 for m in ms if a <= m < b)
    print(f"{k:18s} {n:3d} {w:4d} | {c(-1000,0):4d} {c(-2000,-1000):5d} {c(0,1000):4d} {c(1000,2000):5d} | " + '  '.join(out))
