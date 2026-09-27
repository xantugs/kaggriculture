"""Summarise plan_audit.py rows: value of planned work the controller dropped (unserved / popped by shed stops /
trimmed during the day), by visit type (tag + ops), and the last-day harvests of finished plants among them."""
import sys, json, collections
rows = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
rows = [r for r in rows if r.get('m') is not None]
n = len(rows)
print('games', n)
T = collections.defaultdict(lambda: [0, 0.0])
R = collections.defaultdict(lambda: [0, 0.0])
byday = collections.defaultdict(float)
for r in rows:
    for d, ev in r['days'].items():
        for kind in ('un', 'pop', 'trim'):
            for tag, ops, val, must, x, y, rot in ev[kind]:
                key = (kind, tag, ops)
                T[key][0] += 1; T[key][1] += val
                if rot:
                    R[(kind, int(d))][0] += 1; R[(kind, int(d))][1] += val
                byday[(kind, int(d))] += val
print('dropped work, per game: count, planner value')
for kind in ('un', 'pop', 'trim'):
    tot = sum(v[1] for k, v in T.items() if k[0] == kind); cnt = sum(v[0] for k, v in T.items() if k[0] == kind)
    print(' %-4s %.1f visits  $%.0f' % (kind, cnt / n, tot / n))
    for k, v in sorted(T.items(), key=lambda kv: -kv[1][1]):
        if k[0] == kind and v[1] / n >= 5:
            print('      %-3s %-14s %6.2f  $%7.1f' % (k[1], k[2], v[0] / n, v[1] / n))
print('last-day harvests of finished plants (rot next day), per game:')
for k, v in sorted(R.items()):
    print('   ', k, '%.2f $%.1f' % (v[0] / n, v[1] / n))
print('by day $/game:', {k: round(v / n) for k, v in sorted(byday.items()) if v / n >= 20})
