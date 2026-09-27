"""Summarise shed_probe.py rows: discards per game, and how much of each night's overflow the waitable harvests
(after the unit's last drop) could have covered.   usage: shed_probe_sum.py rows.jsonl [start_by_gid.json]"""
import sys, json, collections, statistics

rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
rows = [r for r in rows if r.get('m') is not None]
n = len(rows)
tot_units = 0; tot_v = 0.0
by_day = collections.Counter(); by_day_v = collections.Counter()
lost_items = collections.Counter(); lost_items_v = collections.Counter()
cover = collections.Counter()      # units of overflow that could be covered by each class (greedy, in class order)
cls_units = collections.Counter()  # waitable units available on overflow nights (after last drop)
nights = 0; games_hit = 0
per_game = []
ORDER = ['A', 'O', 'G', 'F', 'M']
for r in rows:
    gv = 0.0
    for d, nt in r['nights'].items():
        nights += 1
        ovf = nt['ovf']; tot_units += ovf; tot_v += nt['lost_v']; gv += nt['lost_v']
        by_day[int(d)] += ovf; by_day_v[int(d)] += nt['lost_v']
        for k, v in nt['lost'].items():
            lost_items[k] += v; lost_items_v[k] += v * nt['px'].get(k, 0)
        avail = collections.Counter()
        for h in nt['h']:
            avail[h[5]] += h[4]
        for c, v in avail.items():
            cls_units[c] += v
        left = ovf
        for c in ORDER:
            k = min(left, avail.get(c, 0)); cover[c] += k; left -= k
        cover['uncovered'] += left
    per_game.append((gv, r['gid'], r['opp'], r['m']))
    if gv > 0:
        games_hit += 1
print('games %d  nights with a discard %d  games hit %d' % (n, nights, games_hit))
print('discarded units %d (%.1f/game)  $%.0f (%.1f/game)' % (tot_units, tot_units / n, tot_v, tot_v / n))
print('by day units:', dict(sorted(by_day.items())))
print('by day $   :', {k: round(v) for k, v in sorted(by_day_v.items())})
print('lost items :', {k: (v, round(lost_items_v[k])) for k, v in lost_items.most_common()})
print('waitable units after last drop on those nights, by class:', dict(cls_units))
print('overflow covered greedily (A, O, G, F, M order):', dict(cover))
per_game.sort(reverse=True)
print('worst games:', [(round(g), gid, o, m) for g, gid, o, m in per_game[:12]])
tm = [r['tmax'] for r in rows if r.get('tmax') is not None]
if tm:
    print('tmax max %.3f  mean %.3f' % (max(tm), statistics.mean(tm)))
