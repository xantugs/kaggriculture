import sys, os, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diag import load, short, t8rows
A = {(x['gid'], x['seat']): x for x in load(sys.argv[1])}
B = {(x['gid'], x['seat']): x for x in load(sys.argv[2])} if sys.argv[2] != 'T8' else t8rows()
T = t8rows()
ks = [k for k in A if k in B]
ok = [k for k in ks if A[k]['tape'] >= 0.8 * T[k]['rec_tape'] and B[k]['tape'] >= 0.8 * T[k]['rec_tape']]
d_ = sorted(A[k]['m'] - B[k]['m'] for k in ks); q = max(1, len(d_) // 10)
for nm, kk in (('all', ks), ('trim', ok)):
    d = [A[k]['m'] - B[k]['m'] for k in kk]
    if not d: continue
    mu = sum(d) / len(d); sd = (sum((x - mu) ** 2 for x in d) / max(1, len(d) - 1)) ** 0.5
    if nm == 'all':
        tm = d_[q:-q] if len(d_) > 2 * q else d_
        print('   10%%-trimmed mean %+.0f' % (sum(tm) / len(tm)))
    print('%s vs %s %-4s n %3d  delta %+6.0f +- %5.0f  median %+6.0f  wins %d -> %d' % (sys.argv[1], sys.argv[2], nm, len(d), mu, sd / len(d) ** 0.5, statistics.median(d),
          sum(B[k]['m'] > 0 for k in kk), sum(A[k]['m'] > 0 for k in kk)))
