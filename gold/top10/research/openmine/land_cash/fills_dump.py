"""Dump the hourly fills of one seat, days a..b.  usage: fills_dump.py team_or_gid [a b] [role]"""
import sys
from common import load, SHORT
S = load()
key = sys.argv[1]
a, b = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 10)
role = sys.argv[4] if len(sys.argv) > 4 else 'rec'
cand = [s for s in S.values() if s['role'] == role and (str(s['gid']) == key or SHORT.get(s['team']) == key or s['team'] == key)
        and s['date'] >= '2026-09-23']
s = sorted(cand, key=lambda s: -s['gid'])[0]
print(s['team'], s['gid'], s['seat'], 'vs', s['opp'], s['seat_row']['rew'], s['seat_row']['shops'])
for d in range(a, b + 1):
    r = s['days'][d]
    print('--- d%d m0 %.0f mend %.0f mmin %.0f@%s herd %s crops %s shops %s' % (d, r['m0'], r['mend'], r['mmin'], r['mmin_h'],
          r['herd'], r['crops'], r['shops']))
    print('    px', r.get('px'), 'riv$', (r.get('riv') or {}).get('money'))
    line = []
    for f in r.get('fills') or []:
        h, op, it, n, v = f
        line.append('%d:%s %s %d@%.1f' % (h, op, it[:5], n, v / max(1, n)))
    print('   ', ' | '.join(line))
    print('    units', r.get('units'), 'shed', r.get('shed'))
    ops = r.get('ops') or {}
    print('    FERTILIZE', {k: v for k, v in ops.items() if k.startswith('FERTILIZE') or k.startswith('COLLECT_F') or k.startswith('FEED')})
