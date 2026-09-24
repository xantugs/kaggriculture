import json, collections, sys
fn = sys.argv[1]; team = sys.argv[2]
rows = [json.loads(l) for l in open(fn)]
rows = [r for r in rows if r['ok'] and team in r['names']]
P = ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER']
n = len(rows); wins = 0; mar = 0; money = [0, 0]
S = [collections.Counter(), collections.Counter()]; U = [collections.Counter(), collections.Counter()]
B = [collections.Counter(), collections.Counter()]; H = [0, 0]; HN = [0, 0]; L = [0, 0]
for r in rows:
    me = r['names'].index(team); op = 1 - me
    wins += r['rewards'][me] > r['rewards'][op]; mar += r['rewards'][me] - r['rewards'][op]
    for k, s in enumerate((me, op)):
        money[k] += r['rewards'][s]
        for p in P:
            a = r['sales'][s].get(p, [0, 0]); S[k][p] += a[1]; U[k][p] += a[0]
        for kk, v in r['buys'][s].items(): B[k][kk] += v[1]
        H[k] += r['hires'][s][1]; HN[k] += r['hires'][s][0]; L[k] += r['land'][s][1]
print('%s: n %d wins %d (%.0f%%) mean margin %+.0f  money %.0f vs %.0f' % (team, n, wins, 100*wins/n, mar/n, money[0]/n, money[1]/n))
print('%-12s %9s %9s %8s %8s %7s %7s' % ('product', 'rev_me', 'rev_op', 'u_me', 'u_op', 'px_me', 'px_op'))
for p in P:
    print('%-12s %9.0f %9.0f %8.1f %8.1f %7.1f %7.1f' % (p, S[0][p]/n, S[1][p]/n, U[0][p]/n, U[1][p]/n, S[0][p]/max(1,U[0][p]), S[1][p]/max(1,U[1][p])))
print('buys:')
for kk in sorted(set(B[0]) | set(B[1])):
    print('   %-28s %8.0f %8.0f' % (kk, B[0][kk]/n, B[1][kk]/n))
print('hires cost %.0f vs %.0f ; hires %.1f vs %.1f ; land %.0f vs %.0f' % (H[0]/n, H[1]/n, HN[0]/n, HN[1]/n, L[0]/n, L[1]/n))
keys = ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','GOOSE','COW','SHEEP','empty','WEED','COOP','PASTURE']
for day in ['3','6','9','12','15','18','21','24','27']:
    a = collections.Counter(); b = collections.Counter(); m = 0
    for r in rows:
        c = r['comp'].get(day)
        if not c: continue
        me = r['names'].index(team); m += 1
        a.update(c[me] or {}); b.update(c[1-me] or {})
    if m:
        print('day %-2s ME  ' % day, ' '.join('%s:%.1f' % (k[:5], a[k]/m) for k in keys))
        print('       OPP ', ' '.join('%s:%.1f' % (k[:5], b[k]/m) for k in keys))
o = collections.Counter(); t = collections.Counter()
for r in rows:
    me = r['names'].index(team); o.update(r['ops'][me]); t.update(r['ops'][1-me])
print('ops/game me vs opp: ' + ', '.join('%s %.0f/%.0f' % (k, o[k]/n, t[k]/n) for k in sorted(set(o)|set(t), key=lambda k: -(o[k]+t[k]))))
