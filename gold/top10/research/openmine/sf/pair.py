"""Paired gate comparison vs a baseline tag (sf/out/<tag>_gate.jsonl or any rows file).
usage: pair.py base new [product-ledger]"""
import sys, os, json, collections, math
HERE = os.path.dirname(os.path.abspath(__file__))
def load(t):
    f = t if os.path.exists(t) else os.path.join(HERE, 'out', t + '_gate.jsonl')
    return {(r['gid'], r['seat']): r for r in (json.loads(l) for l in open(f, encoding='utf-8'))}
B, N = load(sys.argv[1]), load(sys.argv[2])
keys = [k for k in N if k in B and N[k]['m'] is not None and B[k]['m'] is not None]
by = collections.defaultdict(list)
for k in keys: by[N[k]['team']].append(k)
def stat(ks):
    d = [N[k]['m'] - B[k]['m'] for k in ks]; n = len(d)
    mu = sum(d) / n; sd = math.sqrt(sum((x - mu) ** 2 for x in d) / max(1, n - 1)) / math.sqrt(n) if n > 1 else 0
    return n, mu, sd, sum(B[k]['m'] > 0 for k in ks), sum(N[k]['m'] > 0 for k in ks)
for t, ks in sorted(by.items()) + [('ALL', keys)]:
    n, mu, sd, wb, wn = stat(ks)
    print('%-22s n=%3d  dm %+7.0f +- %5.0f  wins %d -> %d   us %+7.0f  elite %+7.0f' % (t[:22], n, mu, sd, wb, wn,
          sum(N[k]['us'] - B[k]['us'] for k in ks) / n, sum(N[k]['tape'] - B[k]['tape'] for k in ks) / n))
# product ledger deltas (us and elite)
for side in ('led_us', 'led_elite'):
    c = collections.Counter()
    for k in keys:
        for it, v in (N[k].get(side) or {}).items(): c[it] += v / len(keys)
        for it, v in (B[k].get(side) or {}).items(): c[it] -= v / len(keys)
    print(side, 'delta:', ' '.join('%s %+.0f' % (it[:5], v) for it, v in sorted(c.items(), key=lambda x: -abs(x[1]))))
