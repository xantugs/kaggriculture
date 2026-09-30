"""broad_cmp.py TAG : candidate vs c2tr (exact-bytes repro rows) on the old goldg + top10g gates (381 seats): wins, flips, margin,
split by whether the new-meta route fired (tel gc_route == C2S3nm)."""
import json, sys, statistics as st
sys.stdout.reconfigure(encoding='utf-8')
tag = sys.argv[1]; N = 'gold/top10/research/nmloop/'; R = 'gold/top10/research/opening/repro/'
def rows(*ps):
    d = {}
    for p in ps:
        for l in open(p, encoding='utf-8'):
            if l.startswith('{'):
                x = json.loads(l)
                if x.get('m') is not None: d[(x['gid'], x['seat'])] = x
    return d
A = rows(N + 'og_%s_goldg.jsonl' % tag, N + 'og_%s_top10g.jsonl' % tag); B = rows(R + 'main_ctl_c2tr_goldg.jsonl', R + 'main_ctl_c2tr_top10g.jsonl')
them = lambda r: r['us'] - r['m']
ks = [k for k in A if k in B]
for lab, K in (('all', ks), ('route fired (960 band)', [k for k in ks if (A[k].get('tel') or {}).get('gc_route') == 'C2S3nm']),
               ('route not fired', [k for k in ks if (A[k].get('tel') or {}).get('gc_route') != 'C2S3nm'])):
    if not K: print(lab, 'none'); continue
    same = sum(1 for k in K if A[k]['us'] == B[k]['us'] and A[k]['m'] == B[k]['m'])
    up = sum(1 for k in K if A[k]['m'] > 0 and B[k]['m'] <= 0); dn = sum(1 for k in K if B[k]['m'] > 0 and A[k]['m'] <= 0)
    print('%-24s n %3d | identical %3d | wins %s %d vs c2tr %d (+%d/-%d) | margin %+.0f' % (lab, len(K), same, tag, sum(A[k]['m'] > 0 for k in K), sum(B[k]['m'] > 0 for k in K), up, dn, st.mean(A[k]['m'] - B[k]['m'] for k in K)))
