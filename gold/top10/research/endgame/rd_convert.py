"""Convert replay_days.py output (us/them) to day_led.py field names (us/elite) so ana_days/ana_late/ana_verbs read it,
split by live opponent group. usage: rd_convert.py rd.jsonl outprefix  -> outprefix_{copy,own,annex,all}.jsonl"""
import sys, json, csv
G = {int(r['episode_id']): r for r in csv.DictReader(open('replays/live_0926/analysis/games.csv', encoding='utf-8-sig'))}
def grp(g):
    g = G[g]['opp_group']
    return 'copy' if g.startswith('copy (identical') else 'annex' if g.startswith('copy, we diverged') else 'left' if g.startswith('copy, left') else 'own'
out = {k: open(f"{sys.argv[2]}_{k}.jsonl", 'w', encoding='utf-8') for k in ('copy', 'own', 'annex', 'all', 'hi')}
for l in open(sys.argv[1], encoding='utf-8'):
    x = json.loads(l)
    y = dict(x)
    for a, b in (('them', 'elite'), ('days_them', 'days_elite'), ('steps_them', 'steps_elite'), ('final_them', 'final_elite'),
                 ('mkt29_them', 'mkt29_elite'), ('verbs_them', 'verbs_elite')):
        y[b] = y.pop(a)
    s = json.dumps(y, ensure_ascii=False) + '\n'
    g = grp(x['gid'])
    out['all'].write(s)
    if g in out: out[g].write(s)
    if float(G[x['gid']]['opp_rating_before']) >= 2600: out['hi'].write(s)
