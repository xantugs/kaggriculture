"""Paired comparison split by a game-id list (e.g. copy games) and the rest. usage: grpcmp.py base rows.jsonl ids.txt cand [cand...]"""
import sys, json, math, collections
base, f, idf = sys.argv[1], sys.argv[2], sys.argv[3]; cands = sys.argv[4:]
ids = set(int(x) for x in open(idf).read().split())
rows = collections.defaultdict(dict)
for l in open(f, encoding='utf-8'):
    r = json.loads(l)
    if r.get('m') is not None: rows[r['cand']][r['gid']] = r
def st(A, B, keys, lab):
    if not keys: return
    d = [B[k]['m'] - A[k]['m'] for k in keys]; n = len(d); md = sum(d) / n
    se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) if n > 1 else 0
    wa = sum(A[k]['m'] > 0 for k in keys); wb = sum(B[k]['m'] > 0 for k in keys)
    fu = sum(1 for k in keys if A[k]['m'] <= 0 < B[k]['m']); fd = sum(1 for k in keys if B[k]['m'] <= 0 < A[k]['m'])
    print(f'  {lab:8s} n {n:3d}  {md:+6.0f} +- {se:4.0f}  wins {wa} -> {wb} (+{fu}/-{fd})  changed {sum(1 for x in d if abs(x) > .5)}')
for c in cands:
    A, B = rows[base], rows[c]; ks = sorted(k for k in B if k in A)
    print(c, 'vs', base)
    st(A, B, ks, 'all'); st(A, B, [k for k in ks if k in ids], 'copy'); st(A, B, [k for k in ks if k not in ids], 'other')
