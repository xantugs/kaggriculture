"""Paired per-seed comparison of two batch jsonl files (same seeds): mean diff, se, per-product diffs.
usage: paired.py base.jsonl cand.jsonl"""
import sys, json, math
a = {(r['seed'], r['seat']): r for r in map(json.loads, open(sys.argv[1]))}
b = {(r['seed'], r['seat']): r for r in map(json.loads, open(sys.argv[2]))}
ks = [k for k in a if k in b]
d = [b[k]['m'] - a[k]['m'] for k in ks]
n = len(d); m = sum(d) / n; sd = math.sqrt(sum((x - m) ** 2 for x in d) / max(1, n - 1))
print('paired cand-base: mean %+.0f  se %.0f  n %d  better %d worse %d  | base %+.0f cand %+.0f' % (m, sd / math.sqrt(n), n, sum(x > 0 for x in d), sum(x < 0 for x in d), sum(a[k]['m'] for k in ks) / n, sum(b[k]['m'] for k in ks) / n))
keys = sorted(set(k2 for k in ks for k2 in list(b[k]['rev_us']) + list(a[k]['rev_us'])))
print('   ' + ' '.join('%s %+.0f' % (p[:5], sum((b[k]['rev_us'].get(p, 0) - b[k]['rev_them'].get(p, 0)) - (a[k]['rev_us'].get(p, 0) - a[k]['rev_them'].get(p, 0)) for k in ks) / n) for p in keys))
