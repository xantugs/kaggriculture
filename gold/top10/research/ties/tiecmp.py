"""Paired T7-vs-candidate summary for pinned rows with the tie telemetry: all games, games where the layer fired, and
games where it did not. usage: tiecmp.py base_cand cand rows.jsonl[,more]"""
import sys, json, math, collections
base, cand = sys.argv[1], sys.argv[2]
rows = collections.defaultdict(dict)
for f in sys.argv[3].split(','):
    for l in open(f, encoding='utf-8'):
        r = json.loads(l)
        if r.get('m') is None: continue
        rows[r['cand']][(r['gid'], r.get('seat', 0))] = r
A, B = rows[base], rows[cand]
ks = [k for k in B if k in A]
def st(keys, lab):
    if not keys: print(f'  {lab:10s} n 0'); return
    d = [B[k]['m'] - A[k]['m'] for k in keys]; n = len(d); md = sum(d) / n
    se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) if n > 1 else 0
    wa = sum(A[k]['m'] > 0 for k in keys); wb = sum(B[k]['m'] > 0 for k in keys)
    fu = sum(1 for k in keys if A[k]['m'] <= 0 < B[k]['m']); fd = sum(1 for k in keys if B[k]['m'] <= 0 < A[k]['m'])
    print(f'  {lab:10s} n {n:3d}  {md:+6.0f} +- {se:4.0f}  wins {wa} -> {wb} (+{fu}/-{fd})  changed {sum(1 for x in d if abs(x) > .5)}')
fired = [k for k in ks if (B[k].get('tel') or {}).get('gc_tie_blk') or (B[k].get('tel') or {}).get('gc_tie_sort')]
print(cand, 'vs', base)
st(ks, 'all'); st(fired, 'fired'); st([k for k in ks if k not in fired], 'not fired')
t = collections.Counter()
for k in ks:
    for kk, v in (B[k].get('tel') or {}).items():
        if 'tie' in kk and isinstance(v, (int, float)): t[kk] += v
print('  telemetry per game:', {k: round(v / max(1, len(ks)), 2) for k, v in t.items()})
