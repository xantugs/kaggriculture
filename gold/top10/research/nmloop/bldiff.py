"""bldiff.py A B : blind-panel games that differ between candidates A and B (keyed by label, seed, seat): count, mean delta, flips."""
import json, os, sys
N = 'gold/top10/research/nmloop/'
A, B = sys.argv[1], sys.argv[2]
tot = [0, 0, 0.0, 0, 0]
for lab in ('RSTurley', 'SiyuanWang', 'YandG', 'pangzi233'):
    pa, pb = N + 'bl_%s_%s.jsonl' % (A, lab), N + 'bl_%s_%s.jsonl' % (B, lab)
    if not (os.path.exists(pa) and os.path.exists(pb)): continue
    a = {(r['seed'], r['cgt_seat']): r for r in (json.loads(l) for l in open(pa))}
    b = {(r['seed'], r['cgt_seat']): r for r in (json.loads(l) for l in open(pb))}
    ks = [k for k in b if k in a]
    diff = [(k, a[k]['m'], b[k]['m']) for k in ks if abs(a[k]['m'] - b[k]['m']) > 1]
    up = [k for k, x, y in diff if x <= 0 < y]; dn = [k for k, x, y in diff if y <= 0 < x]
    print('%-10s n %2d changed %2d mean delta %+6.0f | flips +%d -%d %s' % (lab, len(ks), len(diff), sum(y - x for k, x, y in diff) / max(1, len(diff)), len(up), len(dn), dn))
    tot[0] += len(ks); tot[1] += len(diff); tot[2] += sum(y - x for k, x, y in diff); tot[3] += len(up); tot[4] += len(dn)
print('total n %d changed %d mean delta %+.0f flips +%d -%d' % (tot[0], tot[1], tot[2] / max(1, tot[1]), tot[3], tot[4]))
