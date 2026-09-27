"""Sales anatomy by day from a PIN_FILLS pinned run: our units/revenue vs the rival's, split copy/divergent.
usage: fills_ana.py pin_fills.jsonl [copy|divergent|all] [day_from]"""
import sys, json, collections
SP = '/home/user/kaggriculture/gold/harness'
rows = [json.loads(l) for l in open(sys.argv[1])]
kind = sys.argv[2] if len(sys.argv) > 2 else 'copy'
d0 = int(sys.argv[3]) if len(sys.argv) > 3 else 16
sims = {int(k): v for k, v in json.load(open(SP + '/simclass.json')).items()}
def div(g):
    s = sims.get(g, {}); return s.get('143', 1) < 0.9 or s.get('359', 1) < 0.8
rows = [r for r in rows if r.get('m') is not None and (kind == 'all' or (kind == 'divergent') == div(r['gid']))]
n = len(rows)
print('%s games: %d  wins %d  mean margin %+.0f' % (kind, n, sum(r['m'] > 0 for r in rows), sum(r['m'] for r in rows) / n))
P = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']
agg = collections.defaultdict(lambda: collections.Counter())   # (day, product) -> counters
buys = collections.defaultdict(lambda: collections.Counter())
for r in rows:
    for step, op, item, price in r['fills']:
        d = step // 24
        if op in ('S', 'rS'):
            agg[(d, item)][op + '_n'] += 1; agg[(d, item)][op + '_$'] += price
        elif op in ('B', 'rB'):
            buys[(d, item)][op + '_n'] += 1; buys[(d, item)][op + '_$'] += price
print('per game averages; delta = us - rival ($)')
print('day  ' + ' '.join('%10s' % p[:9] for p in P) + '     total  cum')
cum = 0.0
for d in range(d0, 30):
    line = []; tot = 0.0
    for p in P:
        c = agg.get((d, p), collections.Counter()); b = buys.get((d, p), collections.Counter())
        dd = (c['S_$'] - c['rS_$'] - b['B_$'] + b['rB_$']) / n
        tot += dd
        line.append('%+10.0f' % dd)
    cum += tot
    print('%3d  ' % d + ' '.join(line) + '  %+8.0f %+6.0f' % (tot, cum))
print()
print('units per game, days %d-29: product  us_units  rival_units  us_$/unit  rival_$/unit' % d0)
for p in P:
    un = sum(agg[(d, p)]['S_n'] for d in range(d0, 30)) / n; rn = sum(agg[(d, p)]['rS_n'] for d in range(d0, 30)) / n
    ud = sum(agg[(d, p)]['S_$'] for d in range(d0, 30)) / n; rd = sum(agg[(d, p)]['rS_$'] for d in range(d0, 30)) / n
    print('  %-11s %8.1f %8.1f   %6.1f %6.1f' % (p, un, rn, ud / un if un else 0, rd / rn if rn else 0))
