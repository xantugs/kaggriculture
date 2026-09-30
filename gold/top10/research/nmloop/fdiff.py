"""fdiff.py A B [GATE] : fresh960 (or f29) seats that differ between candidates A and B: count, mean margin delta, flips, by team."""
import json, os, sys, collections
N = 'gold/top10/research/nmloop/'
A, B = sys.argv[1], sys.argv[2]; pre = sys.argv[3] if len(sys.argv) > 3 else 'f960'
def rows(p): return {(x['gid'], x['seat']): x for x in (json.loads(l) for l in open(p, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None}
a = rows(N + '%s_%s.jsonl' % (pre, A)); b = rows(N + '%s_%s.jsonl' % (pre, B))
ks = [k for k in b if k in a]
diff = [k for k in ks if abs(a[k]['m'] - b[k]['m']) > 1]
up = [k for k in diff if a[k]['m'] <= 0 < b[k]['m']]; dn = [k for k in diff if b[k]['m'] <= 0 < a[k]['m']]
print('%s: n %d changed %d mean delta %+.0f (all seats %+.0f) | wins %d -> %d, flips +%d -%d' % (pre, len(ks), len(diff),
      sum(b[k]['m'] - a[k]['m'] for k in diff) / max(1, len(diff)), sum(b[k]['m'] - a[k]['m'] for k in ks) / max(1, len(ks)),
      sum(a[k]['m'] > 0 for k in ks), sum(b[k]['m'] > 0 for k in ks), len(up), len(dn)))
by = collections.defaultdict(list)
for k in diff: by[b[k]['team']].append(b[k]['m'] - a[k]['m'])
print('  by team:', ' '.join('%s %d %+.0f' % (t[:8], len(v), sum(v) / len(v)) for t, v in sorted(by.items(), key=lambda kv: -len(kv[1]))))
for k in up + dn: print('  flip', k, b[k]['team'], round(a[k]['m']), '->', round(b[k]['m']))
