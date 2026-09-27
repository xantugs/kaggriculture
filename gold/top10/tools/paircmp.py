"""Paired comparison of candidates in one or more pinned/elite rows files, keyed by (gid, seat).
usage: paircmp.py base_cand rows.jsonl[,more] [cand ...]   (cand strings as stored in the rows; default: all others)
Splits by live opponent group when gold/top10/gates/live0926/games.csv knows the gid."""
import sys, json, math, csv, os, collections
base = sys.argv[1]; files = sys.argv[2].split(','); want = sys.argv[3:]
meta = {}
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'gates', 'live0926', 'games.csv')
if os.path.exists(p):
    for r in csv.DictReader(open(p, encoding='utf-8-sig')):
        g = r['opp_group']
        meta[str(r['episode_id'])] = ('copy' if g.startswith('copy (identical') else 'annex' if 'annex' in g else 'own',
                                      '2600+' if float(r['opp_rating_before'] or 0) >= 2600 else '<2600')
rows = collections.defaultdict(dict)
for f in files:
    for l in open(f, encoding='utf-8'):
        r = json.loads(l)
        if r.get('m') is None: continue
        rows[r['cand']][(str(r['gid']), r.get('seat', 0))] = r
cands = want or [c for c in rows if c != base]
def stat(A, B, keys, label):
    if not keys: return
    d = [B[k]['m'] - A[k]['m'] for k in keys]; n = len(d); md = sum(d) / n
    se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) if n > 1 else 0
    wa = sum(A[k]['m'] > 0 for k in keys); wb = sum(B[k]['m'] > 0 for k in keys)
    fu = sum(1 for k in keys if A[k]['m'] <= 0 < B[k]['m']); fd = sum(1 for k in keys if B[k]['m'] <= 0 < A[k]['m'])
    print('  %-14s n %3d  %+7.0f +- %4.0f  wins %3d -> %3d (+%d/-%d)  changed %d' % (label, n, md, se, wa, wb, fu, fd, sum(1 for x in d if abs(x) > 0.5)))
for c in cands:
    A, B = rows[base], rows[c]; ks = [k for k in B if k in A]
    print(c)
    stat(A, B, ks, 'all')
    by = collections.defaultdict(list)
    for k in ks:
        if k[0] in meta: by[meta[k[0]]].append(k)
    for g in sorted(by): stat(A, B, by[g], '%s %s' % g)
    stat(A, B, [k for k in ks if k[0] in meta and meta[k[0]][1] == '2600+'], 'ALL 2600+')
