"""Paired comparison for the night-drop track, with the identity check.
usage: shed_cmp.py base_cand base_rows[,more] cand cand_rows[,more] [ids_file ...]
Prints the paired margin delta (mean +- se), wins and flips on all games and on each ids file given; splits the games
where the fix fired (telemetry gc_shed_skip / gc_shed_perm > 0) from those where it did not; on the latter every
row must equal the baseline (m, us, them, our ledger), else it lists them. tmax of the candidate rows is summarised."""
import sys, json, math, collections

base, bfiles, cand, cfiles = sys.argv[1], sys.argv[2].split(','), sys.argv[3], sys.argv[4].split(',')
idf = sys.argv[5:]


def load(files, c):
    out = {}
    for f in files:
        for l in open(f, encoding='utf-8'):
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get('cand') == c and r.get('m') is not None:
                out[r['gid']] = r
    return out


A = load(bfiles, base); B = load(cfiles, cand)
ks = sorted(k for k in B if k in A)


def stat(keys, label):
    if not keys:
        print('  %-22s n 0' % label); return
    d = [B[k]['m'] - A[k]['m'] for k in keys]; n = len(d); md = sum(d) / n
    se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n) if n > 1 else 0.0
    wa = sum(A[k]['m'] > 0 for k in keys); wb = sum(B[k]['m'] > 0 for k in keys)
    fu = sum(1 for k in keys if A[k]['m'] <= 0 < B[k]['m']); fd = sum(1 for k in keys if B[k]['m'] <= 0 < A[k]['m'])
    print('  %-22s n %3d  %+7.0f +- %4.0f  wins %3d -> %3d (+%d/-%d)  better %d worse %d' % (
        label, n, md, se, wa, wb, fu, fd, sum(1 for x in d if x > 0.5), sum(1 for x in d if x < -0.5)))
    return md, se


def fired(r):
    t = r.get('tel') or {}
    return (t.get('gc_shed_skip', 0) or 0) > 0 or (t.get('gc_shed_perm', 0) or 0) > 0


print(cand, 'vs', base)
stat(ks, 'all')
fk = [k for k in ks if fired(B[k])]; nk = [k for k in ks if not fired(B[k])]
stat(fk, 'fired')
stat(nk, 'not fired')
bad = [k for k in nk if (B[k]['m'], B[k]['us'], B[k]['them']) != (A[k]['m'], A[k]['us'], A[k]['them'])
       or ('led_us' in A[k] and B[k].get('led_us') != A[k].get('led_us'))]
print('  identity on not-fired games: %d of %d identical (m, us, them, our ledger)%s' % (
    len(nk) - len(bad), len(nk), ('  DIFFER: %s' % bad[:20]) if bad else ''))
for f in idf:
    ids = set(int(x) for x in open(f).read().split())
    stat([k for k in ks if k in ids], 'in %s' % f.split('/')[-1])
    stat([k for k in ks if k not in ids], 'not in %s' % f.split('/')[-1])
tm = [B[k].get('tmax') for k in ks if B[k].get('tmax') is not None]
if tm:
    tm.sort()
    print('  cand tmax: max %.3f  p99 %.3f  median %.3f  (n %d)' % (tm[-1], tm[int(0.99 * (len(tm) - 1))], tm[len(tm) // 2], len(tm)))
sk = [(B[k].get('tel') or {}).get('gc_shed_skip_u', 0) or 0 for k in ks]
pm = [(B[k].get('tel') or {}).get('gc_shed_perm', 0) or 0 for k in ks]
print('  skipped units/game %.1f  perm days/game %.2f' % (sum(sk) / max(1, len(ks)), sum(pm) / max(1, len(ks))))
