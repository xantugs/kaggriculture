"""Base vs candidate scan.py rows (same games): identity on games where the fix never fired, escape / care-loss
deltas, tmax. usage: esc_cmp.py base_rows.jsonl cand_rows.jsonl [counter=gc_refill] [min_day=12]"""
import sys, json, math
def load(f):
    return {r['gid']: r for r in map(json.loads, open(f, encoding='utf-8')) if r.get('m') is not None}
A, B = load(sys.argv[1]), load(sys.argv[2])
counter = sys.argv[3] if len(sys.argv) > 3 else 'gc_refill'
d0 = int(sys.argv[4]) if len(sys.argv) > 4 else 12
ks = sorted(k for k in B if k in A)
def fired(r):
    return bool((r.get('tel') or {}).get(counter))
nf = [k for k in ks if not fired(B[k])]
same = [k for k in nf if (A[k]['us'], A[k]['them']) == (B[k]['us'], B[k]['them'])]
print('games %d  fired %d  not fired %d  identical us/them on not-fired %d/%d%s' % (
    len(ks), len(ks) - len(nf), len(nf), len(same), len(nf), '' if len(same) == len(nf) else '  MISMATCH ' + str([k for k in nf if k not in same])))
def agg(r, key, d_min=d0):
    s = 0.0
    for d, ev in r['days'].items():
        if int(d) >= d_min:
            v = ev.get(key)
            if isinstance(v, (int, float)):
                s += v
            elif key == 'esc' and v:
                s += sum(e[-1] for e in v)
            elif key == 'esc_n' and ev.get('esc'):
                s += len(ev['esc'])
    return s
def agg_n(r, d_min=d0):
    return sum(len(ev.get('esc') or []) for d, ev in r['days'].items() if int(d) >= d_min)
def unf(r, d_min=d0):
    return sum(sum((ev.get('unfed') or {}).values()) for d, ev in r['days'].items() if int(d) >= d_min)
n = len(ks)
for lab, f in (('escape $ (d>=%d)' % d0, lambda r: agg(r, 'esc')), ('escape events', agg_n), ('first-strike unfed', unf),
               ('care lost, cared-unfed (carelc_v)', lambda r: agg(r, 'carelc_v')), ('care lost, all (carel_v)', lambda r: agg(r, 'carel_v')),
               ('animal cap (acap_v)', lambda r: agg(r, 'acap_v')), ('night drop (drop_v)', lambda r: agg(r, 'drop_v')),
               ('PASS turns', lambda r: agg(r, 'pass'))):
    a = sum(f(A[k]) for k in ks); b = sum(f(B[k]) for k in ks)
    print('  %-36s base %10.1f  cand %10.1f   per game %+8.2f' % (lab, a, b, (b - a) / n))
d = [B[k]['m'] - A[k]['m'] for k in ks]; md = sum(d) / n
se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n)
wa = sum(A[k]['m'] > 0 for k in ks); wb = sum(B[k]['m'] > 0 for k in ks)
print('margin %+.1f +- %.1f  wins %d -> %d (+%d/-%d)' % (md, se, wa, wb, sum(1 for k in ks if A[k]['m'] <= 0 < B[k]['m']),
                                                    sum(1 for k in ks if B[k]['m'] <= 0 < A[k]['m'])))
ta = sorted(A[k].get('tmax', 0) for k in ks); tb = sorted(B[k].get('tmax', 0) for k in ks)
print('tmax base median %.3f max %.3f | cand median %.3f max %.3f' % (ta[n // 2], ta[-1], tb[n // 2], tb[-1]))
