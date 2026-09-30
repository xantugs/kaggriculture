"""livewatch.py : summary of v34/v35 live games so far: games, W-L, non-DONE statuses (errors/timeouts), latest rating."""
import json, time, collections
rows = [json.loads(l) for l in open('gold/top10/research/opening/live_v3435.jsonl', encoding='utf-8') if l.startswith('{')]
by = collections.defaultdict(lambda: [0, 0, 0, None, []])
for r in sorted(rows, key=lambda r: r['meta'].get('end') or ''):
    m = r['meta']; s = m['seat']; lab = m.get('label')
    v = by[lab]; v[0] += 1
    d = r['rewards'][s] - r['rewards'][1 - s]
    v[1] += d > 0; v[2] += d < 0; v[3] = m.get('our_after')
    if any(st != 'DONE' for st in r['statuses']): v[4].append((r['id'], r['statuses'], m['opp']))
line = ' | '.join('%s: %d games %d-%d rating %s bad %s' % (k, v[0], v[1], v[2], ('%.1f' % v[3]) if v[3] else '-', v[4][:3]) for k, v in sorted(by.items()))
print(time.strftime('%H:%M', time.gmtime()), line or 'no games yet')
