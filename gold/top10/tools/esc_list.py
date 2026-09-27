"""Escapes (and cared-but-unfed care losses) per game from scan.py rows.
usage: esc_list.py rows.jsonl [min_$]   -> table of escape events, per-day totals, opponent group"""
import sys, json, csv, collections
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
mind = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
grp = {}
try:
    for r in csv.DictReader(open('gold/top10/gates/live0926/games.csv', encoding='utf-8-sig')):
        grp[int(r['episode_id'])] = r.get('opp_group', '')
except Exception:
    pass
tot = 0.0; n_ev = 0; byday = collections.Counter(); games = set(); carelc = 0.0; unfed_new = 0
for r in rows:
    if r.get('m') is None:
        continue
    for d, ev in sorted(r['days'].items(), key=lambda x: int(x[0])):
        carelc += ev.get('carelc_v', 0) or 0
        for e in ev.get('esc') or []:
            tot += e[-1]; n_ev += 1; byday[int(d)] += e[-1]
            if e[-1] >= mind:
                games.add(r['gid'])
                print('%d %-20s %-6s d%-2s m %+7.0f  %s placed d%d held %d fut %d @%d,%d  $%d' % (
                    r['gid'], r['opp'][:20], grp.get(r['gid'], '')[:6], d, r['m'], e[0], e[1], e[2], e[3], e[4], e[5], e[6]))
n = len([r for r in rows if r.get('m') is not None])
print('games %d  escape events %d  $%.0f (%.1f/game)  games with an escape >= $%g: %d' % (n, n_ev, tot, tot / max(1, n), mind, len(games)))
print('by day', dict(sorted(byday.items())))
print('cared-but-unfed care loss (carelc_v) $%.0f (%.1f/game)' % (carelc, carelc / max(1, n)))
