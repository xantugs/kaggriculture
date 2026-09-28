"""Paired comparison of gate rows (keyed by gid,seat): pair.py base.jsonl cand.jsonl [cand2 ...]"""
import sys, json, statistics as st
def load(p):
    R = {}
    for l in open(p, encoding='utf-8'):
        if l.strip():
            r = json.loads(l); R[(r['gid'], r.get('seat', 0))] = r
    return R
B = load(sys.argv[1])
for p in sys.argv[2:]:
    C = load(p); ks = [k for k in C if k in B]
    d = [C[k]['m'] - B[k]['m'] for k in ks]
    n = len(d)
    if n < 2:
        print(p, 'n', n); continue
    se = st.pstdev(d) / n ** 0.5
    wb = sum(B[k]['m'] > 0 for k in ks); wc = sum(C[k]['m'] > 0 for k in ks)
    up = sum(B[k]['m'] <= 0 < C[k]['m'] for k in ks); dn = sum(C[k]['m'] <= 0 < B[k]['m'] for k in ks)
    hb = sum(B[k].get('led_us', {}).get('hire', 0) for k in ks) / n; hc = sum(C[k].get('led_us', {}).get('hire', 0) for k in ks) / n
    print(f"{p.split('/')[-1][:40]:40s} n {n:4d} {st.mean(d):+8.0f} +- {se:5.0f}  wins {wb:3d} -> {wc:3d} (+{up}/-{dn})  hire {hb:7.0f} -> {hc:7.0f}")
