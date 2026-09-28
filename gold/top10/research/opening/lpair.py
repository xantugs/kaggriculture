"""lpair.py cand_rows.jsonl [base_rows.jsonl]: paired live comparison vs T8's lv0928 rows (default) by gid."""
import sys, os, json, statistics, glob
HERE = os.path.dirname(os.path.abspath(__file__))
KG = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
A = {r["gid"]: r for r in (json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip().startswith("{")) if r.get("m") is not None}
if len(sys.argv) > 2:
    B = {r['gid']: r for r in map(json.loads, open(sys.argv[2], encoding='utf-8'))}
else:
    B = {}
    for f in glob.glob(os.path.join(KG, 'gold', 'top10', 'gates', 'kout', 'kagg-lv0928-*', 'rows_lv*.jsonl')):
        for r in map(json.loads, open(f, encoding='utf-8')):
            if r.get('cand') == 'T8':
                B[r['gid']] = r
ks = [k for k in A if k in B]
def st(kk, nm):
    if not kk: return
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
keys = sorted({k for g in ks for k in list(A[g]['led_us']) + list(B[g]['led_us'])})
print('our ledger delta:   ' + '  '.join('%s %+.0f' % (k[:5], sum(A[g]['led_us'].get(k, 0) - B[g]['led_us'].get(k, 0) for g in ks) / len(ks)) for k in keys))
print('rival ledger delta: ' + '  '.join('%s %+.0f' % (k[:5], sum(A[g]['led_them'].get(k, 0) - B[g]['led_them'].get(k, 0) for g in ks) / len(ks)) for k in keys))
errs = [k for k in ks if A[k].get('err') and any(A[k]['err'])]
print('errors:', len(errs), errs[:5])
