"""Compare variants against 'default' world by world. usage: ana_variants.py results.jsonl [mined.json]
Excludes a mined route's own source world. Splits by opponent class (opp_class.json)."""
import sys, json, collections
rs = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8')]
src = {}
if len(sys.argv) > 2:
    meta = json.load(open(sys.argv[2], encoding='utf-8'))['meta']
    src = {'m%s' % k: v['gid'] for k, v in meta.items()}
cls = {}
try:
    for r in json.load(open('opp_class.json', encoding='utf-8')):
        cls[r['gid']] = 'mirror15' if r['sim359'] >= 0.8 else ('mirror6' if r['sim143'] >= 0.9 else 'other')
except Exception:
    pass
by = collections.defaultdict(dict)
shops = {}
for r in rs:
    by[r['gid']][r['label']] = r['m']
    shops[r['gid']] = tuple(r['shops'][:2]) if r.get('shops') else None
labels = sorted(set(l for v in by.values() for l in v if l != 'default'))
rows = []
for l in labels:
    d = []; flips_w = flips_l = 0; per = collections.defaultdict(list)
    for g, v in by.items():
        if l not in v or 'default' not in v or src.get(l) == g:
            continue
        dd = v[l] - v['default']; d.append(dd); per[cls.get(g, '?')].append(dd)
        if v['default'] <= 0 < v[l]: flips_w += 1
        if v['default'] > 0 >= v[l]: flips_l += 1
    if d:
        rows.append((sum(d) / len(d), l, len(d), flips_w, flips_l, {k: (len(x), round(sum(x) / len(x))) for k, x in per.items()}))
rows.sort(reverse=True)
print(f"{'label':16s} {'mean d':>8s} {'n':>4s} {'+W':>4s} {'-W':>4s}  by class")
for m, l, n, fw, fl, pc in rows:
    print(f"{l:16s} {m:+8.0f} {n:4d} {fw:4d} {fl:4d}  {pc}")
dm = [v['default'] for v in by.values() if 'default' in v]
print('default: n', len(dm), 'wins', sum(x > 0 for x in dm), 'mean', round(sum(dm) / max(1, len(dm))))
