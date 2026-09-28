import sys, json, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diag import load, short, mean
for tag in sys.argv[1:]:
    X = load(tag)
    for lo, hi in ((0, 9), (10, 15), (16, 29)):
        out = []
        for side in ('ours', 'elite'):
            c = collections.Counter(); b = collections.Counter()
            for x in X:
                for D in x[side][lo:hi + 1]:
                    for k, v in D['sell'].items(): c[k] += v[1] / len(X)
                    for k, v in D['bp'].items(): b[k] += v[1] / len(X)
                    for k, v in D['bs'].items(): b['seed:' + k] += v[1] / len(X)
                    for k, v in D['ba'].items(): b['an:' + k] += v[1] / len(X)
                    b['wage'] += D['wage'] / len(X)
            out.append((side, c, b))
        print('==', tag, 'days %d-%d' % (lo, hi))
        keys = sorted(set(out[0][1]) | set(out[1][1]))
        print('  sell  ' + '  '.join('%s %6.0f/%6.0f' % (k[:5], out[0][1][k], out[1][1][k]) for k in keys))
        keys = sorted(set(out[0][2]) | set(out[1][2]))
        print('  buy   ' + '  '.join('%s %5.0f/%5.0f' % (k[:9], out[0][2][k], out[1][2][k]) for k in keys))
