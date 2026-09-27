"""Paired comparison of elite-gate rows: candidate files vs a baseline file (same gid, seat).
usage: paired_gate.py base.jsonl cand1.jsonl [cand2.jsonl ...]"""
import sys, json, math, collections
def load(p):
    d = {}
    for l in open(p, encoding='utf-8'):
        r = json.loads(l)
        if r.get('m') is not None: d[(r['gid'], r['seat'])] = r
    return d
B = load(sys.argv[1])
for p in sys.argv[2:]:
    C = load(p)
    ks = [k for k in C if k in B]
    if not ks: print(p, 'no overlap'); continue
    d = [C[k]['m'] - B[k]['m'] for k in ks]
    n = len(d); mu = sum(d) / n; sd = math.sqrt(sum((x - mu) ** 2 for x in d) / max(1, n - 1)); se = sd / math.sqrt(n)
    wb = sum(B[k]['m'] > 0 for k in ks); wc = sum(C[k]['m'] > 0 for k in ks)
    up = sum(1 for k in ks if B[k]['m'] <= 0 < C[k]['m']); dn = sum(1 for k in ks if C[k]['m'] <= 0 < B[k]['m'])
    ch = sum(1 for x in d if abs(x) > 1)
    led = collections.Counter(); lede = collections.Counter()
    for k in ks:
        for kk, v in C[k]['led_us'].items(): led[kk] += v
        for kk, v in B[k]['led_us'].items(): led[kk] -= v
        for kk, v in C[k]['led_elite'].items(): lede[kk] += v
        for kk, v in B[k]['led_elite'].items(): lede[kk] -= v
    print(f"{p.split('/')[-1]:22s} n={n:3d} margin {mu:+7.0f} +- {se:4.0f}  wins {wb}->{wc} (+{up}/-{dn})  changed {ch}")
    print('    us   :', ' '.join(f"{k[:5]} {v/n:+.0f}" for k, v in sorted(led.items(), key=lambda kv: kv[1])))
    print('    elite:', ' '.join(f"{k[:5]} {v/n:+.0f}" for k, v in sorted(lede.items(), key=lambda kv: kv[1])))
