"""clpair.py A.jsonl B.jsonl : paired closed-loop comparison (same seed+seat), B minus A."""
import json, sys, statistics as st
def rows(p):
    out = {}
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l.startswith('{'): continue
        try: r = json.loads(l)
        except Exception: continue
        if r.get('m') is None: continue
        out[(r.get('seed'), r.get('seat'))] = r
    return out
A, B = rows(sys.argv[1]), rows(sys.argv[2])
ks = sorted(k for k in B if k in A)
d = [B[k]['m'] - A[k]['m'] for k in ks]
if not d: print('no pairs'); sys.exit()
se = st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else 0
wa, wb = sum(A[k]['m'] > 0 for k in ks), sum(B[k]['m'] > 0 for k in ks)
da, db = sum(A[k]['m'] == 0 for k in ks), sum(B[k]['m'] == 0 for k in ks)
ea, eb = sum(1 for k in ks if any(A[k].get('err') or [])), sum(1 for k in ks if any(B[k].get('err') or []))
print('n %d  delta %+.0f +- %.0f  median %+.0f  wins %d -> %d  draws %d -> %d  errs %d/%d  (us %+.0f them %+.0f)' % (
    len(d), st.mean(d), se, st.median(d), wa, wb, da, db, ea, eb,
    st.mean(float(B[k]['us']) - float(A[k]['us']) for k in ks) if 'us' in B[ks[0]] else 0, st.mean(float(B[k]['them']) - float(A[k]['them']) for k in ks) if 'them' in B[ks[0]] else 0))
