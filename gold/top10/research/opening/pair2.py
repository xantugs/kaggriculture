"""pair2.py A.jsonl B.jsonl [key=gid|gidseat] : paired B minus A on common games, overall and split by B's router class (tel gc_route)."""
import json, sys, statistics as st, collections
def rows(p, key):
    out = {}
    for l in open(p, encoding='utf-8'):
        l = l.strip()
        if not l.startswith('{'): continue
        try: r = json.loads(l)
        except Exception: continue
        if r.get('m') is None: continue
        k = str(r['gid']) if key == 'gid' else (str(r['gid']), r.get('seat', 0))
        out[k] = r
    return out
key = sys.argv[3] if len(sys.argv) > 3 else 'gid'
A, B = rows(sys.argv[1], key), rows(sys.argv[2], key)
ks = [k for k in B if k in A]
def line(name, kk):
    if not kk: return
    d = [B[k]['m'] - A[k]['m'] for k in kk]
    se = st.stdev(d) / len(d) ** 0.5 if len(d) > 1 else 0
    print('%-10s n %3d delta %+6.0f +- %4.0f median %+6.0f wins %3d -> %3d  identical %3d  (us %+6.0f them %+6.0f)' % (
        name, len(d), st.mean(d), se, st.median(d), sum(A[k]['m'] > 0 for k in kk), sum(B[k]['m'] > 0 for k in kk),
        sum(1 for k in kk if abs(B[k]['us'] - A[k]['us']) < 1), st.mean(B[k]['us'] - A[k]['us'] for k in kk), st.mean(B[k]['them'] - A[k]['them'] for k in kk) if 'them' in B[kk[0]] else 0))
line('all', ks)
by = collections.defaultdict(list)
for k in ks: by[(B[k].get('tel') or {}).get('gc_route', '?')].append(k)
for c, kk in sorted(by.items(), key=lambda kv: -len(kv[1])): line(c, kk)
