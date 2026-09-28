"""Compact paired table of tp candidates vs T8 (tp_diag rows in out/): elite OW (goldg, top10g, pooled) and live."""
import json, math, collections, os, sys
O = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
def load(f):
    p = os.path.join(O, f)
    if not os.path.exists(p): return {}
    return {(str(r['gid']), r.get('seat', 0)): r for r in map(json.loads, open(p, encoding='utf-8')) if r.get('m') is not None}
def st(A, B, keys):
    d = [B[k]['m'] - A[k]['m'] for k in keys]; n = len(d)
    if not n: return '-'
    md = sum(d) / n; se = math.sqrt(sum((x - md) ** 2 for x in d) / max(1, n - 1) / n)
    wa = sum(A[k]['m'] > 0 for k in keys); wb = sum(B[k]['m'] > 0 for k in keys)
    return '%+5.0f+-%3.0f %3d>%3d' % (md, se, wa, wb)
def kind(r):
    t = r.get('tel') or {}
    return 'copy' if (not t.get('gc_div2') and t.get('gc_ad_step', -1) in (-1, None)) else 'div'
cands = sys.argv[1:] or ['TP_A3', 'TP_A1', 'TP_A31', 'TP_A3f', 'TP_A1f', 'TP_A31f']
bg, bt, bl = load('goldg_T8.jsonl'), load('top10g_T8.jsonl'), load('live_T8.jsonl')
print('%-8s | %-17s %-17s %-17s | %-17s %-17s %-17s %-17s' % ('cand', 'goldg OW (56)', 'top10g OW (60)', 'elite OW (116)', 'live (159)', 'live 2600+', 'live copy', 'live div'))
for c in cands:
    g, t, l = load('goldg_%s.jsonl' % c), load('top10g_%s.jsonl' % c), load('live_%s.jsonl' % c)
    E = dict(bg); E.update(bt); EC = dict(g); EC.update(t)
    kl = [k for k in l if k in bl]
    print('%-8s | %-17s %-17s %-17s | %-17s %-17s %-17s %-17s' % (c, st(bg, g, [k for k in g if k in bg]), st(bt, t, [k for k in t if k in bt]),
          st(E, EC, [k for k in EC if k in E]), st(bl, l, kl), st(bl, l, [k for k in kl if (bl[k].get('opp_before') or 0) >= 2600]),
          st(bl, l, [k for k in kl if kind(bl[k]) == 'copy']), st(bl, l, [k for k in kl if kind(bl[k]) == 'div'])))
