"""Summarise hybrid-mirror rows against sf8 rows on the same seats.
usage: hyb_summary.py gate   (reads gapday_<gate>_sf8.jsonl and gapday_hyb{12,16,22,30}_<gate>.jsonl next to this file)"""
import sys, os, json, math, statistics as st, collections
H = os.path.dirname(os.path.abspath(__file__))
g = sys.argv[1]


def rows(p):
    out = {}
    for l in open(p, encoding='utf-8'):
        if not l.strip(): continue
        x = json.loads(l)
        out[(x['gid'], x['seat'])] = dict(team=x['team'], m=x['m'], us=x['us'], el=x['elite'])
    return out


base = rows(os.path.join(H, 'gapday_%s_sf8.jsonl' % g))
print('gate', g, 'sf8 all rows: n %d mean m %+.0f win %.0f%%' % (len(base), st.mean(v['m'] for v in base.values()),
                                                                  100 * st.mean(v['m'] > 0 for v in base.values())))
for D in (12, 16, 22, 30):
    p = os.path.join(H, 'gapday_hyb%d_%s.jsonl' % (D, g))
    if not os.path.exists(p): continue
    h = rows(p)
    ks = [k for k in h if k in base and h[k]['m'] is not None and base[k]['m'] is not None]
    mh = [h[k]['m'] for k in ks]; mb = [base[k]['m'] for k in ks]
    d = [a - b for a, b in zip(mh, mb)]
    se = lambda v: st.pstdev(v) / math.sqrt(len(v))
    print('D %2d  n %3d  hybrid m %+6.0f +-%4.0f win %3.0f%% | sf8 same seats m %+6.0f +-%4.0f win %3.0f%% | '
          'state gap at D (sf8 - hyb) %+6.0f +-%4.0f | elite final hyb %.0f sf8 %.0f | us final hyb %.0f sf8 %.0f' % (
              D, len(ks), st.mean(mh), se(mh), 100 * st.mean(m > 0 for m in mh), st.mean(mb), se(mb),
              100 * st.mean(m > 0 for m in mb), st.mean(d), se(d), st.mean(h[k]['el'] for k in ks),
              st.mean(base[k]['el'] for k in ks), st.mean(h[k]['us'] for k in ks), st.mean(base[k]['us'] for k in ks)))
    bt = collections.defaultdict(list)
    for k in ks: bt[h[k]['team']].append((h[k]['m'], base[k]['m']))
    print('      by team (hyb / sf8): ' + '  '.join('%s %+.0f/%+.0f' % (t[:12], st.mean(a for a, b in v), st.mean(b for a, b in v))
                                                   for t, v in bt.items()))
