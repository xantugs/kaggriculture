"""Paired comparison of two candidates in a pinned run, split by rival type (copy vs divergent).
usage: pair_ana.py run.jsonl candA candB"""
import sys, json, math, collections
SP = '/home/user/kaggriculture/gold/harness'
rows = [json.loads(l) for l in open(sys.argv[1])]
A, B = sys.argv[2], sys.argv[3]
sims = {int(k): v for k, v in json.load(open(SP + '/simclass.json')).items()}
sc = {}
for f in ['/home/user/kaggriculture/moon/our_eps.json', '/home/user/kaggriculture/moon/our_eps2.json']:
    for e in json.load(open(f)):
        if 'offhand' in e['teams']:
            sc[e['id']] = e['score'][1 - e['teams'].index('offhand')] or 0
by = collections.defaultdict(dict)
for r in rows:
    if r['m'] is None: continue
    key = 'A' if r['cand'].endswith(A) else ('B' if r['cand'].endswith(B) else None)
    if key: by[r['gid']][key] = r
def div(g):
    s = sims.get(g, {})
    return s.get('143', s.get(143, 1)) < 0.9 or s.get('359', s.get(359, 1)) < 0.8
groups = collections.defaultdict(list)
for g, d in by.items():
    if 'A' not in d or 'B' not in d: continue
    t = 'divergent' if div(g) else 'copy'
    groups[t].append((d['A']['m'], d['B']['m'], sc.get(g, 0)))
    groups['all'].append((d['A']['m'], d['B']['m'], sc.get(g, 0)))
    if sc.get(g, 0) >= 2800: groups['opp>=2800'].append((d['A']['m'], d['B']['m'], sc.get(g, 0)))
for t in ('all', 'copy', 'divergent', 'opp>=2800'):
    v = groups[t]
    if not v: continue
    n = len(v); wa = sum(a > 0 for a, b, _ in v); wb = sum(b > 0 for a, b, _ in v)
    d = [b - a for a, b, _ in v]; md = sum(d) / n
    sd = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1)); se = sd / math.sqrt(n)
    flips_up = sum(a <= 0 < b for a, b, _ in v); flips_dn = sum(b <= 0 < a for a, b, _ in v)
    print('%-10s n=%3d  %s wins %3d  %s wins %3d  mean margin %s %+6.0f  %s %+6.0f  diff %+5.0f +- %.0f (z %+.1f)  flips +%d/-%d  changed %d' % (
        t, n, A[:14], wa, B[:14], wb, A[:6], sum(a for a, _, _ in v) / n, B[:6], sum(b for _, b, _ in v) / n, md, se, md / se if se else 0, flips_up, flips_dn, sum(1 for x in d if x != 0)))
