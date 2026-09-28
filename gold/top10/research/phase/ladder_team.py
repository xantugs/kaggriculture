"""Per-team hybrid ladder: sf8 full-game margin, controller-from-D margins, state gap at 16 (sf8 - hyb16) and the elite's
edge after 16 (= -hyb16), with SEs. usage: ladder_team.py gate [prefix]"""
import sys, os, json, math, statistics as st, collections
H = os.path.dirname(os.path.abspath(__file__))
g = sys.argv[1]; pre = sys.argv[2] if len(sys.argv) > 2 else 'gapday_hyb'; bsuf = sys.argv[3] if len(sys.argv) > 3 else 'sf8'


def rows(p):
    return {(x['gid'], x['seat']): (x['team'], x['m']) for x in map(json.loads, (l for l in open(p, encoding='utf-8') if l.strip()))}


base = rows(os.path.join(H, 'gapday_%s_%s.jsonl' % (g, bsuf)))
hy = {D: rows(os.path.join(H, '%s%d_%s.jsonl' % (pre, D, g))) for D in (12, 16, 22)}
ks = [k for k in base if all(k in hy[D] for D in hy)]
se = lambda v: st.pstdev(v) / math.sqrt(len(v)) if len(v) > 1 else 0
bt = collections.defaultdict(list)
for k in ks: bt[base[k][0]].append(k)
print('%-22s %2s | %-15s | %-15s %-15s %-15s | %-17s | %-15s' % ('team', 'n', 'sf8 m', 'ctl from 12', 'ctl from 16', 'ctl from 22', 'state gap @16', 'edge 16-29'))
for t, kk in sorted(bt.items(), key=lambda kv: st.mean(base[k][1] for k in kv[1])):
    m = [base[k][1] for k in kk]; h12 = [hy[12][k][1] for k in kk]; h16 = [hy[16][k][1] for k in kk]; h22 = [hy[22][k][1] for k in kk]
    sg = [a - b for a, b in zip(m, h16)]
    print('%-22s %2d | %+6.0f +-%5.0f | %+6.0f +-%5.0f %+6.0f +-%5.0f %+6.0f +-%5.0f | %+7.0f +-%5.0f | %+6.0f' % (
        t[:22], len(kk), st.mean(m), se(m), st.mean(h12), se(h12), st.mean(h16), se(h16), st.mean(h22), se(h22), st.mean(sg), se(sg), st.mean(h16)))
