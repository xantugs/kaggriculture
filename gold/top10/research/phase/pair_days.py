"""Paired comparison of two gapday_play row files (same seats): final margin and per-day net cash-flow change (cand - base),
plus our sell-through of premium goods on the takeover days. usage: pair_days.py base.jsonl cand.jsonl [d0 d1]"""
import sys, json, math, statistics as st
b = {(x['gid'], x['seat']): x for x in map(json.loads, (l for l in open(sys.argv[1], encoding='utf-8') if l.strip()))}
c = {(x['gid'], x['seat']): x for x in map(json.loads, (l for l in open(sys.argv[2], encoding='utf-8') if l.strip()))}
d0, d1 = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (14, 20)
ks = [k for k in c if k in b]
se = lambda v: st.pstdev(v) / math.sqrt(len(v))
dm = [c[k]['m'] - b[k]['m'] for k in ks]
print('n %d base m %+.0f cand m %+.0f diff %+.0f +- %.0f wins %d -> %d changed %d' % (
    len(ks), st.mean(b[k]['m'] for k in ks), st.mean(c[k]['m'] for k in ks), st.mean(dm), se(dm),
    sum(b[k]['m'] > 0 for k in ks), sum(c[k]['m'] > 0 for k in ks), sum(1 for x in dm if abs(x) > 1)))
def net(f):
    return sum(v for k, v in f.items() if k.startswith('S$')) - sum(v for k, v in f.items() if k.startswith(('B$', 'seed$', 'anim$')) or k in ('land$', 'hire$'))
for D in range(d0, d1):
    du = [net(c[k]['days_us'][D]['f']) - net(b[k]['days_us'][D]['f']) for k in ks]
    de = [net(c[k]['days_elite'][D]['f']) - net(b[k]['days_elite'][D]['f']) for k in ks]
    st_ = []
    for x in (b, c):
        h = sum(x[k]['days_us'][D]['f'].get('hv_' + p, 0) for k in ks for p in ('STRAWBERRY', 'MILK', 'WOOL'))
        s = sum(x[k]['days_us'][D]['f'].get('Su' + p, 0) for k in ks for p in ('STRAWBERRY', 'MILK', 'WOOL'))
        hires = sum(x[k]['days_us'][D]['f'].get('hire$', 0) for k in ks) / len(ks)
        st_.append('sold/harv %.2f hires$ %.0f' % (s / max(1, h), hires))
    print('d%2d our net %+5.0f +-%4.0f  elite net %+5.0f | base %s | cand %s' % (D, st.mean(du), se(du), st.mean(de), st_[0], st_[1]))
