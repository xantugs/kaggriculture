"""azrs2.py DUMP : per day from day 12, our crop tiles and the rival's crop tiles and sales by product, run A vs run B."""
import sys, json, collections
z = json.load(open(sys.argv[1]))
A, B = z['A'], z['B']
def g(R, who, d): return R[who].get(str(d)) or {}
def crops(r): return ' '.join('%s%d' % (k[:2], v) for k, v in sorted((r.get('crops') or {}).items()))
def sells(r): return ' '.join('%s%d/$%.0f' % (k[:2], v[0], v[1]) for k, v in sorted((r.get('sell') or {}).items()))
tot = {'A': collections.Counter(), 'B': collections.Counter()}; totu = {'A': collections.Counter(), 'B': collections.Counter()}
for d in range(0, 30):
    for tag, R in (('A', A), ('B', B)):
        for k, v in (g(R, 'riv', d).get('sell') or {}).items():
            if d >= 14: tot[tag][k] += v[1]
        for k, v in (g(R, 'us', d).get('sell') or {}).items():
            if d >= 14: totu[tag][k] += v[1]
for d in range(12, 30):
    print('d%-2d us A [%s] | us B [%s]' % (d, crops(g(A, 'us', d)), crops(g(B, 'us', d))))
    print('    riv A [%s] sells %s' % (crops(g(A, 'riv', d)), sells(g(A, 'riv', d))))
    print('    riv B [%s] sells %s' % (crops(g(B, 'riv', d)), sells(g(B, 'riv', d))))
print('days 14-29 revenue by product:')
for k in sorted(set(tot['A']) | set(tot['B']) | set(totu['A']) | set(totu['B'])):
    print('  %-10s us A %7.0f B %7.0f (%+6.0f) | riv A %7.0f B %7.0f (%+6.0f)' % (k, totu['A'][k], totu['B'][k], totu['B'][k] - totu['A'][k], tot['A'][k], tot['B'][k], tot['B'][k] - tot['A'][k]))
