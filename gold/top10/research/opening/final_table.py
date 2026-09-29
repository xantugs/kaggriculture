"""final_table.py : (1) reproduction: the exact upload bytes (repro/*) vs the frozen gate rows of the cands builds, seat by seat;
(2) the final win table on the elite gates (opponent-stable seats, rival class from the c2tr router telemetry): wins, losses,
shared losses, FW-only and T8-only wins, per class; (3) exact-bytes reacting smoke rows per opponent."""
import json, os, sys, glob, collections, statistics as st
sys.stdout.reconfigure(encoding='utf-8')
O = 'gold/top10/research/opening/'
def rows(p): return [x for x in (json.loads(l) for l in open(p, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None] if os.path.exists(p) else []
def ek(*ps):
    d = {}
    for p in ps: d.update({(x['gid'], x['seat']): x for x in rows(O + p)})
    return d
def them(r): return r['us'] - r['m']
rp = {f: ek('repro/main_ctl_%s_goldg.jsonl' % f, 'repro/main_ctl_%s_top10g.jsonl' % f) for f in ('FWt', 'T8fcWt', 'c2tr')}
fw0 = ek('fg_FWt_goldg.jsonl', 'fg_FWt_top10g.jsonl'); c20 = ek('fg_c2tr_goldg.jsonl', 'fg_c2tr_top10g.jsonl'); hf0 = ek('r4_T8fcWt_hf60.jsonl')
cls = {k: (c20[k].get('tel') or {}).get('gc_route') for k in c20}
t80 = {k: (hf0[k] if cls[k] == 'herdfirst' else c20[k]) for k in c20 if cls[k] != 'herdfirst' or k in hf0}
print('(1) REPRODUCTION (exact upload bytes vs frozen rows of the gated cands builds):')
for f, ref in (('FWt', fw0), ('T8fcWt', t80), ('c2tr', c20)):
    ks = [k for k in rp[f] if k in ref]
    same = sum(1 for k in ks if rp[f][k]['us'] == ref[k]['us'] and rp[f][k]['m'] == ref[k]['m'])
    w_new = sum(rp[f][k]['m'] > 0 for k in ks); w_old = sum(ref[k]['m'] > 0 for k in ks)
    g = [k for k in ks if k in ek('fg_c2tr_goldg.jsonl')]
    print('   %-7s seats %3d, identical us+margin %3d, wins now %3d vs frozen %3d  (goldg %d / top10g %d now; frozen %d / %d); errors %d' % (
        f, len(ks), same, w_new, w_old, sum(rp[f][k]['m'] > 0 for k in g), w_new - sum(rp[f][k]['m'] > 0 for k in g),
        sum(ref[k]['m'] > 0 for k in g), w_old - sum(ref[k]['m'] > 0 for k in g), sum(1 for k in ks if any(rp[f][k].get('err') or []))))
    diff = [k for k in ks if not (rp[f][k]['us'] == ref[k]['us'] and rp[f][k]['m'] == ref[k]['m'])]
    for k in diff[:6]: print('      differs', k, ref[k]['us'], ref[k]['m'], '->', rp[f][k]['us'], rp[f][k]['m'])
A, B, C = rp['FWt'], rp['T8fcWt'], (rp['c2tr'] if len(rp['c2tr']) >= len(c20) else c20)
print('   (c2tr columns below from %s rows)' % ('exact-bytes' if len(rp['c2tr']) >= len(c20) else 'frozen cands'))
ks = [k for k in A if k in B and k in C]
stable = [k for k in ks if abs(them(A[k]) - them(B[k])) <= 0.2 * max(1, them(B[k]))]
print('\n(2) FINAL WIN TABLE, elite goldg+top10g, exact bytes, opponent-stable seats %d of %d' % (len(stable), len(ks)))
print('   %-10s %4s | %-15s | %-15s | %-15s | %6s %7s %7s | %s' % ('class', 'n', 'FWt W/L', 'T8fcWt W/L', 'c2tr W/L', 'shared', 'FW-only', 'T8-only', 'c2tr vs T8fcWt only-wins'))
tot = collections.Counter()
for c in ('chassis', 'C2S3', 'herdpoor', 'herdfirst', 'majkel', 'other', None):
    kk = [k for k in stable if cls.get(k) == c]
    if not kk: continue
    aw = sum(A[k]['m'] > 0 for k in kk); bw = sum(B[k]['m'] > 0 for k in kk); cw = sum(C[k]['m'] > 0 for k in kk)
    sh = sum(1 for k in kk if A[k]['m'] <= 0 and B[k]['m'] <= 0)
    ao = sum(1 for k in kk if A[k]['m'] > 0 and B[k]['m'] <= 0); bo = sum(1 for k in kk if B[k]['m'] > 0 and A[k]['m'] <= 0)
    co = sum(1 for k in kk if C[k]['m'] > 0 and B[k]['m'] <= 0); bo2 = sum(1 for k in kk if B[k]['m'] > 0 and C[k]['m'] <= 0)
    for n_, v in (('n', len(kk)), ('aw', aw), ('bw', bw), ('cw', cw), ('sh', sh), ('ao', ao), ('bo', bo), ('co', co), ('bo2', bo2)): tot[n_] += v
    print('   %-10s %4d | %3d W %3d L     | %3d W %3d L     | %3d W %3d L     | %6d %7d %7d | %d / %d' % (c, len(kk), aw, len(kk) - aw, bw, len(kk) - bw, cw, len(kk) - cw, sh, ao, bo, co, bo2))
t = tot
print('   %-10s %4d | %3d W %3d L     | %3d W %3d L     | %3d W %3d L     | %6d %7d %7d | %d / %d' % ('TOTAL', t['n'], t['aw'], t['n'] - t['aw'], t['bw'], t['n'] - t['bw'], t['cw'], t['n'] - t['cw'], t['sh'], t['ao'], t['bo'], t['co'], t['bo2']))
print('   either tape wins (best-of-two coverage): %d of %d' % (sum(1 for k in stable if A[k]['m'] > 0 or B[k]['m'] > 0), len(stable)))
print('\n(3) EXACT-BYTES REACTING SMOKE (both seats; W/T/L; max step s):')
for f in ('main_ctl_FWt', 'main_ctl_T8fcWt', 'main_ctl_c2tr'):
    by = collections.defaultdict(list)
    for p in glob.glob(O + 'preflight/%s_*.jsonl' % f):
        for r in rows(p): by[os.path.basename(r['b'])].append(r)
    n = sum(len(v) for v in by.values()); w = sum(r['us'] > r['them'] for v in by.values() for r in v); tt = sum(r['us'] == r['them'] for v in by.values() for r in v)
    print('   %s: %d games, %d W %d T %d L, errors %d' % (f, n, w, tt, n - w - tt, sum(1 for v in by.values() for r in v if any(r.get('err') or []))))
    print('      ' + '; '.join('%s %d/%d' % (k.replace('x_kaggriculture-', '').replace('.py', '')[:16], sum(r['us'] > r['them'] for r in v), len(v)) for k, v in sorted(by.items())))
print('\n(4) COMMON-LOSS AUDIT (stable seats lost by both FWt and T8fcWt), by team and by product ledger (FWt us - elite, mean $):')
sh = [k for k in stable if A[k]['m'] <= 0 and B[k]['m'] <= 0]
tm = collections.defaultdict(lambda: [0, 0])
for k in stable:
    tm[str(A[k].get('team'))][1] += 1
    if k in sh: tm[str(A[k].get('team'))][0] += 1
print('   shared losses %d of %d stable seats' % (len(sh), len(stable)))
print('   ' + '; '.join('%s %d/%d' % (t[:14], a, b) for t, (a, b) in sorted(tm.items(), key=lambda kv: -kv[1][1]) if b >= 5))
led = collections.defaultdict(list)
for k in sh:
    lu, le = A[k].get('led_us') or {}, A[k].get('led_elite') or {}
    for p in set(lu) | set(le): led[p].append(lu.get(p, 0) - le.get(p, 0))
print('   ' + ', '.join('%s %+.0f' % (p, sum(v) / len(sh)) for p, v in sorted(led.items(), key=lambda kv: sum(kv[1]))))
print('   mean margin on shared losses %+.0f; median %+.0f' % (st.mean(A[k]['m'] for k in sh), st.median(A[k]['m'] for k in sh)))
