"""Paired comparison with ledger deltas: candidate rows vs baseline rows keyed by (gid, seat).
usage: pairled.py base_rows.jsonl cand_rows.jsonl [more cand rows ...]"""
import sys, json, math, collections
base = {(r['gid'], r['seat']): r for r in map(json.loads, open(sys.argv[1], encoding='utf-8')) if r.get('m') is not None}
for f in sys.argv[2:]:
    rows = [r for r in map(json.loads, open(f, encoding='utf-8')) if r.get('m') is not None]
    ks = [(r['gid'], r['seat']) for r in rows if (r['gid'], r['seat']) in base]
    C = {(r['gid'], r['seat']): r for r in rows}
    d = [C[k]['m'] - base[k]['m'] for k in ks]; n = len(d)
    if not n:
        print(f, 'no paired rows'); continue
    md = sum(d) / n; se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) if n > 1 else 0
    wa = sum(base[k]['m'] > 0 for k in ks); wb = sum(C[k]['m'] > 0 for k in ks)
    fu = sum(1 for k in ks if base[k]['m'] <= 0 < C[k]['m']); fd = sum(1 for k in ks if C[k]['m'] <= 0 < base[k]['m'])
    ch = sum(1 for x in d if abs(x) > 0.5)
    print('%s\n  n %d  delta %+.0f +- %.0f  wins %d -> %d (+%d/-%d)  changed %d  errs %d  tmax %.2f' % (
        f, n, md, se, wa, wb, fu, fd, ch, sum(1 for k in ks if any(C[k].get('err') or [])), max(max(C[k].get('tmax') or [0]) for k in ks)))
    for side in ('led_us', 'led_elite'):
        acc = collections.Counter()
        for k in ks:
            for p, v in C[k].get(side, {}).items(): acc[p] += v
            for p, v in base[k].get(side, {}).items(): acc[p] -= v
        print('  %-9s %s' % (side, '  '.join('%s %+.0f' % (p, v / n) for p, v in sorted(acc.items(), key=lambda kv: -abs(kv[1])) if abs(v / n) >= 20)))
    print('  us %+.0f  elite %+.0f' % (sum(C[k]['us'] - base[k]['us'] for k in ks) / n, sum(C[k]['tape'] - base[k]['tape'] for k in ks) / n))
