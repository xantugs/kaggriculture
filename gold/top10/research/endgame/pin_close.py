"""Paired margin distribution of two pinned row files (same gid): close-loss/close-win counts, flips.
usage: pin_close.py base.jsonl cand.jsonl [base_cand_filter]"""
import sys, json, math
def load(p, cand=None):
    d = {}
    for l in open(p, encoding='utf-8'):
        r = json.loads(l)
        if cand and r.get('cand') != cand: continue
        d[r['gid']] = r
    return d
B = load(sys.argv[1], sys.argv[3] if len(sys.argv) > 3 else None); C = load(sys.argv[2])
ks = [k for k in C if k in B]
bins = [-1e9, -5000, -3000, -2000, -1000, 0, 1000, 2000, 3000, 5000, 1e9]
def hist(ms):
    c = [0] * (len(bins) - 1)
    for m in ms:
        for i in range(len(bins) - 1):
            if bins[i] <= m < bins[i + 1]: c[i] += 1
    return ' '.join(f"{c[i]:3d}" for i in range(len(c)))
print('n', len(ks), ' bins:', ' '.join(f"{int(b/1000) if abs(b)<1e8 else 'inf'}k" for b in bins))
for nm, D in (('base', B), ('cand', C)):
    ms = [D[k]['m'] for k in ks]
    print(f"{nm:5s} W={sum(m>0 for m in ms):3d} | {hist(ms)}")
d = [C[k]['m'] - B[k]['m'] for k in ks]; mu = sum(d) / len(d); sd = math.sqrt(sum((x - mu) ** 2 for x in d) / (len(d) - 1))
print(f"paired {mu:+.0f} +- {sd/math.sqrt(len(d)):.0f} (sd {sd:.0f}); flips +{sum(1 for k in ks if B[k]['m']<=0<C[k]['m'])}/-{sum(1 for k in ks if C[k]['m']<=0<B[k]['m'])}")
