"""Paired comparison of tp_diag rows (candidate vs base on the same (gid, seat)) with the SPEC test-plan diagnostics.
usage: tp_cmp.py base.jsonl[,more] cand.jsonl[,more] [label]"""
import sys, json, math, collections


def load(files):
    out = {}
    for f in files.split(','):
        for l in open(f, encoding='utf-8'):
            r = json.loads(l)
            if r.get('m') is None:
                continue
            out[(str(r['gid']), r.get('seat', 0))] = r
    return out


def stat(A, B, keys):
    d = [B[k]['m'] - A[k]['m'] for k in keys]; n = len(d)
    if not n:
        return 'n 0'
    md = sum(d) / n
    se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) if n > 1 else 0
    wa = sum(A[k]['m'] > 0 for k in keys); wb = sum(B[k]['m'] > 0 for k in keys)
    fu = sum(1 for k in keys if A[k]['m'] <= 0 < B[k]['m']); fd = sum(1 for k in keys if B[k]['m'] <= 0 < A[k]['m'])
    return 'n %3d  %+7.0f +- %4.0f (z %+.1f)  wins %3d -> %3d (+%d/-%d)  changed %d' % (
        n, md, se, md / se if se else 0, wa, wb, fu, fd, sum(1 for x in d if abs(x) > 0.5))


def main():
    A = load(sys.argv[1]); B = load(sys.argv[2]); label = sys.argv[3] if len(sys.argv) > 3 else ''
    keys = [k for k in B if k in A]
    print('==', label, sys.argv[2].split('/')[-1], 'vs', sys.argv[1].split('/')[-1])
    print('  all            ', stat(A, B, keys))
    by = collections.defaultdict(list)
    for k in keys:
        by[B[k].get('team') or ('2600+' if (B[k].get('opp_before') or 0) >= 2600 else '<2600')].append(k)
    for t in sorted(by, key=lambda t: -len(by[t])):
        print('  %-15s' % t[:15], stat(A, B, by[t]))
    # ---- diagnostics
    def dsum(rows, f):
        c = collections.Counter()
        for r in rows:
            for d, v in (r.get('diag', {}).get(f) or {}).items():
                if isinstance(v, dict):
                    for k2, n in v.items():
                        c[(int(d), k2)] += n
                else:
                    c[int(d)] += v
        return c
    ra = [A[k] for k in keys]; rb = [B[k] for k in keys]
    ba, bb = dsum(ra, 'bounce'), dsum(rb, 'bounce')
    kinds = sorted(set(k2 for (d, k2) in list(ba) + list(bb)))
    print('  bounced tape orders by day (base -> cand), days 0-16:')
    for k2 in kinds:
        row = ['%d:%d>%d' % (d, ba.get((d, k2), 0), bb.get((d, k2), 0)) for d in range(17) if ba.get((d, k2), 0) or bb.get((d, k2), 0)]
        diff = sum(bb.get((d, k2), 0) - ba.get((d, k2), 0) for d in range(17))
        print('    %-14s diff %+d  %s' % (k2, diff, ' '.join(row)))
    ca, cb = dsum(ra, 'cap'), dsum(rb, 'cap')
    print('  orders beyond 10 (days 0-16): base %d cand %d' % (sum(ca.values()), sum(cb.values())))
    ea, eb = dsum(ra, 'esc'), dsum(rb, 'esc')
    print('  escapes days 0-16: base %d cand %d | all days: base %d cand %d' % (
        sum(v for d, v in ea.items() if d <= 16), sum(v for d, v in eb.items() if d <= 16), sum(ea.values()), sum(eb.values())))
    def se_buys(rows):
        return sum(1 for r in rows for s, q, c in (r.get('diag', {}).get('land') or []) if q >= 3 and s < 17 * 24)
    def land_days(rows):
        c = collections.Counter()
        for r in rows:
            for s, q, cash in (r.get('diag', {}).get('land') or []):
                c[(q, s // 24)] += 1
        return c
    print('  SE purchases before day 17: base %d cand %d' % (se_buys(ra), se_buys(rb)))
    la, lb = land_days(ra), land_days(rb)
    if la != lb:
        print('  land (quads_before, day) base', dict(sorted(la.items())), '\n                          cand', dict(sorted(lb.items())))
    def mean_d16(rows, k):
        v = [r.get('diag', {}).get('d16', {}).get(k, 0) for r in rows]
        return sum(v) / max(1, len(v))
    print('  day-16 snapshot (mean): ' + '  '.join('%s %.2f>%.2f' % (k[2:] if k[1] == '_' else k, mean_d16(ra, k), mean_d16(rb, k))
                                             for k in ('P_STRAWBERRY', 'P_WHEAT', 'P_TOMATO', 'A_GOOSE', 'A_COW', 'A_SHEEP', 'E_COOP', 'E_PASTURE', 'WEED', 'money')))
    m0a, m0b = collections.defaultdict(list), collections.defaultdict(list)
    for r in ra:
        for d, v in (r.get('diag', {}).get('m0') or {}).items(): m0a[int(d)].append(v)
    for r in rb:
        for d, v in (r.get('diag', {}).get('m0') or {}).items(): m0b[int(d)].append(v)
    print('  hour-0 cash d3-10 (mean): ' + ' '.join('d%d %.0f>%.0f' % (d, sum(m0a[d]) / max(1, len(m0a[d])), sum(m0b[d]) / max(1, len(m0b[d]))) for d in range(3, 11)))
    # telemetry
    tel = collections.Counter(); strs = collections.Counter()
    for r in rb:
        for k, v in (r.get('tel') or {}).items():
            if k.startswith('tp_'):
                if isinstance(v, (int, float)):
                    tel[k] += v
                else:
                    strs[k] += 1
    print('  tp telemetry sums:', ' '.join('%s=%g' % (k[3:], v) for k, v in sorted(tel.items())))
    print('  tp string fields present in n games:', ' '.join('%s=%d' % (k[3:], v) for k, v in sorted(strs.items())))
    fired = sum(1 for r in rb if any(k.startswith('tp_conv_') and k not in ('tp_conv_lost', 'tp_conv_noseed', 'tp_conv_tiles') for k in (r.get('tel') or {})))
    print('  games with a conversion: %d of %d' % (fired, len(rb)))
    flips = collections.Counter()
    for k in keys:
        ta, tb = A[k].get('tel') or {}, B[k].get('tel') or {}
        for f in ('gc_start', 'gc_rich', 'gc_ad_step', 'gc_div2', 'gc_s2t', 'gc_s2t_ext'):
            if ta.get(f) != tb.get(f):
                flips[f] += 1
    print('  classification/takeover differences (games):', dict(flips))
    # ledger
    la_, lb_ = collections.Counter(), collections.Counter(); ea_, eb_ = collections.Counter(), collections.Counter()
    for k in keys:
        for x, y in (('led_us', la_), ('led_elite', ea_), ('led_them', ea_)):
            for p, v in (A[k].get(x) or {}).items(): y[p] += v
        for x, y in (('led_us', lb_), ('led_elite', eb_), ('led_them', eb_)):
            for p, v in (B[k].get(x) or {}).items(): y[p] += v
    n = max(1, len(keys))
    print('  ledger delta us  :', ' '.join('%s %+.0f' % (p[:5], (lb_[p] - la_[p]) / n) for p in sorted(set(la_) | set(lb_)) if abs(lb_[p] - la_[p]) / n >= 1))
    print('  ledger delta them:', ' '.join('%s %+.0f' % (p[:5], (eb_[p] - ea_[p]) / n) for p in sorted(set(ea_) | set(eb_)) if abs(eb_[p] - ea_[p]) / n >= 1))


if __name__ == '__main__':
    main()
