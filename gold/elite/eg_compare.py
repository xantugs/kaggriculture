"""Paired comparison of elite-gate runs against a baseline run.
usage: eg_compare.py base_name cand_name [cand_name ...]   (names without the eg_ prefix / .jsonl suffix)
Rows are keyed (gid, seat); m = our cash - elite cash on the same seat."""
import sys, json, math, collections
D = '/home/user/kaggriculture/gold/elite/'
def load(name):
    out = {}
    for l in open(D + 'eg_%s.jsonl' % name):
        r = json.loads(l)
        if r.get('m') is None: continue
        out[(r['gid'], r['seat'])] = r
    return out
base = load(sys.argv[1])
print('%-22s n    wins(base/cand)  us     elite   margin  diff +- se   z    flips   tel(sold/held/wait)' % 'candidate')
for name in sys.argv[2:]:
    try: x = load(name)
    except FileNotFoundError: print(name, 'missing'); continue
    keys = sorted(set(base) & set(x))
    if not keys: print(name, 'no overlap'); continue
    n = len(keys)
    d = [x[k]['m'] - base[k]['m'] for k in keys]
    md = sum(d) / n; sd = math.sqrt(sum((v - md) ** 2 for v in d) / max(1, n - 1)); se = sd / math.sqrt(n)
    wb = sum(base[k]['m'] > 0 for k in keys); wc = sum(x[k]['m'] > 0 for k in keys)
    up = sum(base[k]['m'] <= 0 < x[k]['m'] for k in keys); dn = sum(x[k]['m'] <= 0 < base[k]['m'] for k in keys)
    us = sum(x[k]['us'] - base[k]['us'] for k in keys) / n
    el = sum((x[k]['us'] - x[k]['m']) - (base[k]['us'] - base[k]['m']) for k in keys) / n
    tel = collections.Counter()
    for k in keys:
        for t in ('gc_dp_sold', 'gc_dp_held', 'gc_dp_wait'):
            tel[t] += x[k].get('tel', {}).get(t, 0)
    print('%-22s %3d  %3d/%3d          %+6.0f %+6.0f  %+6.0f  %+5.0f +- %3.0f  %+4.1f  +%d/-%d  %d/%d/%d' % (
        name, n, wb, wc, us, el, sum(x[k]['m'] for k in keys) / n, md, se, md / se if se else 0, up, dn,
        tel['gc_dp_sold'] // n, tel['gc_dp_held'] // n, tel['gc_dp_wait'] // n))
