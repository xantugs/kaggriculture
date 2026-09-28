"""Pair live rows (pinned4 output) vs the T8 S=0 baseline. usage: livepair.py new.jsonl [base.jsonl]"""
import sys, json, math, collections
new = sys.argv[1]; base = sys.argv[2] if len(sys.argv) > 2 else 'gold/top10/gates/live0927_S0_T8.jsonl'
B = {r['gid']: r for r in (json.loads(l) for l in open(base, encoding='utf-8'))}
N = {r['gid']: r for r in (json.loads(l) for l in open(new, encoding='utf-8'))}
ks = [g for g in N if g in B and N[g]['m'] is not None and B[g]['m'] is not None]
d = [N[g]['m'] - B[g]['m'] for g in ks]; n = len(d); mu = sum(d) / n
se = math.sqrt(sum((x - mu) ** 2 for x in d) / max(1, n - 1) / n)
print('n=%d dm %+.0f +- %.0f  wins %d -> %d  dus %+.0f  dthem %+.0f' % (n, mu, se, sum(B[g]['m'] > 0 for g in ks), sum(N[g]['m'] > 0 for g in ks),
      sum(N[g]['us'] - B[g]['us'] for g in ks) / n, sum(N[g]['them'] - B[g]['them'] for g in ks) / n))
for side in ('led_us', 'led_them'):
    c = collections.Counter()
    for g in ks:
        for it, v in (N[g][side] or {}).items(): c[it] += v / n
        for it, v in (B[g][side] or {}).items(): c[it] -= v / n
    print(side, ' '.join('%s %+.0f' % (it[:5], v) for it, v in sorted(c.items(), key=lambda x: -abs(x[1])) if abs(v) > 100))
