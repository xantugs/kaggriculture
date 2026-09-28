import sys, json, statistics
A = {r['gid']: r for r in map(json.loads, open(sys.argv[1], encoding='utf-8'))}
B = {r['gid']: r for r in map(json.loads, open(sys.argv[2], encoding='utf-8'))}
ks = [k for k in A if k in B]
def st(kk, nm):
    d = [A[k]['m'] - B[k]['m'] for k in kk]
    mu = sum(d) / len(d); sd = (sum((x - mu) ** 2 for x in d) / max(1, len(d) - 1)) ** 0.5
    ds = sorted(d); q = max(1, len(ds) // 10); tm = ds[q:-q]
    print('%-5s n %3d delta %+6.0f +- %5.0f median %+6.0f trim10 %+6.0f  wins %d -> %d  (us %+.0f them %+.0f)' % (nm, len(d), mu, sd / len(d) ** 0.5, statistics.median(d), sum(tm) / len(tm),
          sum(B[k]['m'] > 0 for k in kk), sum(A[k]['m'] > 0 for k in kk), sum(A[k]['us'] - B[k]['us'] for k in kk) / len(kk), sum(A[k]['them'] - B[k]['them'] for k in kk) / len(kk)))
st(ks, 'all')
col = [k for k in ks if A[k]['them'] < 0.75 * B[k]['them']]
print('opponent collapses (them < 75% of base):', len(col))
st([k for k in ks if k not in col], 'trim')
flips = [(k, B[k]['m'], A[k]['m']) for k in ks if (A[k]['m'] > 0) != (B[k]['m'] > 0)]
print('flips +%d / -%d' % (sum(1 for k, b, a in flips if a > 0), sum(1 for k, b, a in flips if a <= 0)))
