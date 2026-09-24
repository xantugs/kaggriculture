import sys, json, collections
R = [json.loads(l) for l in open(sys.argv[1])]
base = sys.argv[2]
S = int(sys.argv[3]) if len(sys.argv) > 3 else None
if S is not None: R = [r for r in R if r['S'] == S]
idx = {(r['gid'], r['team'], r['cand']): r for r in R}
for c in sorted({r['cand'] for r in R}):
    if c == base: continue
    rows = [(r, idx.get((r['gid'], r['team'], base))) for r in R if r['cand'] == c]
    rows = [(a, b) for a, b in rows if b]
    if not rows: continue
    d = [a['m'] - b['m'] for a, b in rows]; du = [a['us'] - b['us'] for a, b in rows]
    cw = sum(a['m'] > 0 for a, b in rows); bw = sum(b['m'] > 0 for a, b in rows)
    fl = sum(a['m'] > 0 >= b['m'] for a, b in rows); rg = sum(b['m'] > 0 >= a['m'] for a, b in rows)
    agg = collections.Counter()
    for a, b in rows:
        for k, v in a['rep'].items(): agg[k] += v
    print(f"{c.split('/')[-1]:14s} n={len(rows):3d} margin {sum(d)/len(d):+7.0f} money {sum(du)/len(du):+7.0f} | W {cw:3d} vs base {bw:3d} | flips +{fl} -{rg} | {dict((k, round(v/len(rows),1)) for k, v in agg.items())}")
