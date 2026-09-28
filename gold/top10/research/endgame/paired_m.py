"""Paired margins of candidate gate rows against a baseline file keyed by (gid, seat) (any row format with m).
usage: paired_m.py base.jsonl cand.jsonl [...]"""
import sys, json, math
def load(p):
    return {(r['gid'], r.get('seat')): r for r in map(json.loads, open(p, encoding='utf-8')) if r.get('m') is not None}
B = load(sys.argv[1])
for p in sys.argv[2:]:
    C = load(p); ks = [k for k in C if k in B]
    d = [C[k]['m'] - B[k]['m'] for k in ks]; n = len(d); mu = sum(d) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in d) / max(1, n - 1))
    up = sum(1 for k in ks if B[k]['m'] <= 0 < C[k]['m']); dn = sum(1 for k in ks if C[k]['m'] <= 0 < B[k]['m'])
    ch = sum(1 for x in d if abs(x) > 1)
    led = {}
    if 'led_us' in C[ks[0]] and 'days_us' in B[ks[0]]:
        pass
    print(f"{p.split('/')[-1]:24s} n={n} paired {mu:+.0f} +- {sd/math.sqrt(n):.0f} (sd {sd:.0f})  wins {sum(B[k]['m']>0 for k in ks)} -> {sum(C[k]['m']>0 for k in ks)} (+{up}/-{dn})  changed {ch}")
