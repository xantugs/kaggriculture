"""Paired comparison vs a base cand. usage: pair.py base_substr file[,file...]  (rows from pinned4 or elite_gate; cand field groups)"""
import sys, json, math, collections
base = sys.argv[1]
rows = [json.loads(l) for p in sys.argv[2].split(',') for l in open(p, encoding='utf-8')]
by = collections.defaultdict(dict)
for r in rows:
    if r.get('m') is None: continue
    by[r['cand']][(r['gid'], r.get('seat'))] = r
bk = [c for c in by if c == base] or [c for c in by if base in c]
assert len(bk) == 1, (bk, list(by))
B = by[bk[0]]
print(f"base {bk[0]}: n={len(B)} wins {sum(r['m']>0 for r in B.values())} mean m {sum(r['m'] for r in B.values())/len(B):+.0f}")
for c, C in by.items():
    if c == bk[0]: continue
    ks = [k for k in C if k in B]
    d = [C[k]['m'] - B[k]['m'] for k in ks]; n = len(d); mu = sum(d) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in d) / max(1, n - 1))
    up = sum(1 for k in ks if B[k]['m'] <= 0 < C[k]['m']); dn = sum(1 for k in ks if C[k]['m'] <= 0 < B[k]['m'])
    ch = sum(1 for x in d if abs(x) > 1)
    hb = [B[k].get('led_us', {}).get('hire') for k in ks]; hc = [C[k].get('led_us', {}).get('hire') for k in ks]
    hs = ''
    if all(x is not None for x in hb + hc):
        hs = f" hire {sum(hc)/n - sum(hb)/n:+.0f}"
    tel = collections.Counter()
    for k in ks:
        for kk, v in (C[k].get('tel') or {}).items():
            if ('pack' in kk or 'd27' in kk or 'lev' in kk or 'ehs' in kk) and isinstance(v, (int, float)): tel[kk] += v
    print(f"{c.split('/')[-1]:26s} n={n} paired {mu:+.0f} +- {sd/math.sqrt(n):.0f}  wins {sum(B[k]['m']>0 for k in ks)} -> {sum(C[k]['m']>0 for k in ks)} (+{up}/-{dn}) changed {ch}{hs}  tel/game { {k: round(v/n,2) for k, v in sorted(tel.items())} }")
