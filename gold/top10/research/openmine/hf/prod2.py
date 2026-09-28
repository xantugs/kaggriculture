"""prod2.py tagA tagB: our net cash flows per product and phase, A vs B on the same seats (and the elite's)."""
import sys, json, collections, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diag import load
A = {(x['gid'], x['seat']): x for x in load(sys.argv[1])}
B = {(x['gid'], x['seat']): x for x in load(sys.argv[2])}
keys = [k for k in A if k in B and A[k]['tape'] >= 0.6 * B[k]['tape']]
print(len(keys), 'seats')
def flows(x, side, lo, hi):
    c = collections.Counter()
    for D in x[side][lo:hi + 1]:
        for k, v in D['sell'].items(): c[k] += v[1]
        for k, v in D['bp'].items(): c[k] -= v[1]
        for k, v in D['bs'].items(): c['seed'] -= v[1]
        for k, v in D['ba'].items(): c['anim'] -= v[1]
        c['wage'] -= D['wage']
        for l in D['land']: c['land'] -= {'NE': 1000, 'SW': 2000, 'SE': 4000}[l[0]]
    return c
for lo, hi in ((0, 7), (8, 11), (12, 15), (16, 22), (23, 29)):
    ca = collections.Counter(); cb = collections.Counter(); ea = collections.Counter(); eb = collections.Counter()
    for k in keys:
        for kk, v in flows(A[k], 'ours', lo, hi).items(): ca[kk] += v / len(keys)
        for kk, v in flows(B[k], 'ours', lo, hi).items(): cb[kk] += v / len(keys)
        for kk, v in flows(A[k], 'elite', lo, hi).items(): ea[kk] += v / len(keys)
        for kk, v in flows(B[k], 'elite', lo, hi).items(): eb[kk] += v / len(keys)
    ks = sorted(set(ca) | set(cb))
    print('days %2d-%2d  ours A-B total %+6.0f : ' % (lo, hi, sum(ca.values()) - sum(cb.values())) + ' '.join('%s %+.0f' % (k[:5], ca[k] - cb[k]) for k in ks if abs(ca[k] - cb[k]) >= 50))
    ks = sorted(set(ea) | set(eb))
    print('            elite A-B total %+6.0f : ' % (sum(ea.values()) - sum(eb.values())) + ' '.join('%s %+.0f' % (k[:5], ea[k] - eb[k]) for k in ks if abs(ea[k] - eb[k]) >= 50))
