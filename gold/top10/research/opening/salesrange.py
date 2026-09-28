"""salesrange.py tag [tag2 ...] [--ranges 0-9,10-16,17-29]: product sales $ (net of purchases for WHEAT/FERTILIZER) per day range,
ours vs elite, from diag compact rows (out_<tag>.jsonl in hf/ or opening/)."""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
def load(tag):
    for d in (HERE, os.path.join(os.path.dirname(HERE), 'openmine', 'hf')):
        f = os.path.join(d, 'out_%s.jsonl' % tag)
        if os.path.exists(f):
            return [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]
    raise SystemExit('no rows for ' + tag)
args = sys.argv[1:]
ranges = [(0, 9), (10, 16), (17, 29)]
if '--ranges' in args:
    i = args.index('--ranges'); ranges = [tuple(int(v) for v in r.split('-')) for r in args[i + 1].split(',')]; args = args[:i] + args[i + 2:]
P = ['STRAWBERRY', 'MELON', 'MILK', 'WOOL', 'EGG', 'FERTILIZER', 'WHEAT', 'TOMATO', 'CARROT']
for tag in args:
    X = load(tag)
    n = len(X)
    print('== %s (%d seats)  us %.0f  elite %.0f  margin %+.0f' % (tag, n, sum(x['us'] for x in X) / n, sum(x['tape'] for x in X) / n, sum(x['m'] for x in X) / n))
    for side in ('ours', 'elite'):
        for d0, d1 in ranges:
            c = collections.Counter(); bp = collections.Counter(); seed = 0; anim = 0; wage = 0; land = 0
            for x in X:
                for D in x[side][d0:d1 + 1]:
                    for k, v in D['sell'].items(): c[k] += v[1]
                    for k, v in (D.get('bp') or {}).items(): bp[k] += v[1]
                    seed += sum(v[1] for v in (D.get('bs') or {}).values())
                    anim += sum(v[1] for v in (D.get('ba') or {}).values())
                    wage += D['wage']
                    land += sum(l[2] if False else 0 for l in D['land'])
            m0 = sum(x[side][d0]['m0'] for x in X) / n; m1 = sum(x[side][d1]['mend'] for x in X) / n
            print('  %-5s d%2d-%2d cash %6.0f -> %6.0f (%+6.0f) | ' % (side, d0, d1, m0, m1, m1 - m0) +
                  ' '.join('%s %5.0f' % (p[:4], (c[p] - bp[p]) / n) for p in P) + ' | seed %5.0f anim %5.0f wage %4.0f' % (seed / n, anim / n, wage / n))
