"""f29_report.py [CANDS...] : the fresh29 held-out report ChatGPT asked for (L19c).
960-band seats (the elite's step-1 money 940-980, no hands), opponent-stable vs the tape (CGt), per candidate:
wins, L->W / W->L vs the tape, net, median margin delta, losses within $3k; margin quantiles and near-miss counts;
NMp44 - NMp26 split by 3+ strawberry buyers among the first 5 shops; wage and strawberry deltas; per-team rows;
the melon-state proxy (NMp26 differs from NMp13 <=> the 12-melon rule fired); all-seat totals and tape W -> cand L
outside the band."""
import json, os, sys, statistics as st, collections
sys.stdout.reconfigure(encoding='utf-8')
N = 'gold/top10/research/nmloop/'; G = 'gold/top10/gates/'
SB = ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET")
refs = {}
for l in open(G + 'fresh29_refs.jsonl', encoding='utf-8'):
    r = json.loads(l); refs[(r['gid'], r['seat'])] = r
def band(k):
    r = refs[k]; m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
    return 940 <= m <= 980 and h == 0
def rows(p):
    if not os.path.exists(p): return {}
    return {(x['gid'], x['seat']): x for x in (json.loads(l) for l in open(p, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None}
T = rows(N + 'f29_TAPE.jsonl')
cands = sys.argv[1:] or ['NMp13', 'NMp26', 'NMp44']
R = {c: rows(N + 'f29_%s.jsonl' % c) for c in cands}
them = lambda r: r['us'] - r['m']
def stable(A, ks): return [k for k in ks if abs(them(A[k]) - them(T[k])) <= 0.2 * max(1, them(T[k]))]
def q(xs, p):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(p * (len(xs) - 1) + 0.5))] if xs else float('nan')
nb = sum(1 for k in refs if band(k))
print('fresh29: %d seats, 960-band %d; tape rows %d (%s)' % (len(refs), nb, len(T), ' '.join('%s %d' % (c, len(R[c])) for c in cands)))
print('\n960-band, stable vs tape:')
print('  %-6s %5s %5s %4s %4s %4s %8s %9s | quantiles of our margin P25/median/P75 | |m|<=3k 5k 10k' % ('cand', 'n', 'wins', 'L>W', 'W>L', 'net', 'medianD', 'tape wins'))
for c in cands:
    A = R[c]; ks = [k for k in A if k in T and band(k)]; s = stable(A, ks)
    if not s: print('  %-6s no rows' % c); continue
    lw = sum(1 for k in s if T[k]['m'] <= 0 < A[k]['m']); wl = sum(1 for k in s if A[k]['m'] <= 0 < T[k]['m'])
    ms = [A[k]['m'] for k in s]
    print('  %-6s %5d %5d %4d %4d %+4d %+8.0f %9d | %+7.0f %+7.0f %+7.0f | %3d %3d %3d' % (c, len(s), sum(m > 0 for m in ms), lw, wl, lw - wl,
          st.median(A[k]['m'] - T[k]['m'] for k in s), sum(T[k]['m'] > 0 for k in s), q(ms, .25), q(ms, .5), q(ms, .75),
          sum(abs(m) <= 3000 for m in ms), sum(abs(m) <= 5000 for m in ms), sum(abs(m) <= 10000 for m in ms)))
    print('         mean margin delta %+.0f, our cash %+.0f; wages %+.0f, strawberry %+.0f (cand - tape, per seat)' % (
          st.mean(A[k]['m'] - T[k]['m'] for k in s), st.mean(A[k]['us'] - T[k]['us'] for k in s),
          st.mean(A[k]['led_us'].get('hire', 0) - T[k]['led_us'].get('hire', 0) for k in s),
          st.mean(A[k]['led_us'].get('STRAWBERRY', 0) - T[k]['led_us'].get('STRAWBERRY', 0) for k in s)))
if 'NMp44' in R and 'NMp26' in R and R['NMp44'] and R['NMp26']:
    A, B = R['NMp26'], R['NMp44']
    print('\nNMp44 - NMp26 on 960-band seats, split by strawberry buyers among the first 5 shops:')
    for name, cond in (('>= 3 buyers', lambda n: n >= 3), ('< 3 buyers', lambda n: n < 3)):
        ks = [k for k in B if k in A and band(k) and cond(sum(s in SB for s in refs[k]['shops'][:5]))]
        if not ks: continue
        ch = [k for k in ks if abs(B[k]['m'] - A[k]['m']) > 1]
        print('  %-11s n %3d changed %3d | wins %d -> %d (L>W %d, W>L %d) | mean delta %+.0f (changed %+.0f) | wages %+.0f strawberry %+.0f' % (
            name, len(ks), len(ch), sum(A[k]['m'] > 0 for k in ks), sum(B[k]['m'] > 0 for k in ks),
            sum(1 for k in ks if A[k]['m'] <= 0 < B[k]['m']), sum(1 for k in ks if B[k]['m'] <= 0 < A[k]['m']),
            st.mean(B[k]['m'] - A[k]['m'] for k in ks), st.mean(B[k]['m'] - A[k]['m'] for k in ch) if ch else 0.0,
            st.mean(B[k]['led_us'].get('hire', 0) - A[k]['led_us'].get('hire', 0) for k in ks),
            st.mean(B[k]['led_us'].get('STRAWBERRY', 0) - A[k]['led_us'].get('STRAWBERRY', 0) for k in ks)))
if 'NMp26' in R and 'NMp13' in R and R['NMp26'] and R['NMp13']:
    A, B = R['NMp13'], R['NMp26']
    ks = [k for k in B if k in A and band(k)]
    fired = [k for k in ks if abs(B[k]['m'] - A[k]['m']) > 1]; nf = [k for k in ks if k not in fired]
    print('\nmelon-state proxy (NMp26 != NMp13 <=> the 12-melon rule changed the game): fired %d, not %d' % (len(fired), len(nf)))
    for name, ss in (('fired', fired), ('not fired', nf)):
        if ss:
            print('  %-9s NMp26 - tape %+.0f, NMp13 - tape %+.0f, NMp26 - NMp13 %+.0f | wins tape %d NMp13 %d NMp26 %d' % (name,
                st.mean(B[k]['m'] - T[k]['m'] for k in ss if k in T), st.mean(A[k]['m'] - T[k]['m'] for k in ss if k in T), st.mean(B[k]['m'] - A[k]['m'] for k in ss),
                sum(T[k]['m'] > 0 for k in ss if k in T), sum(A[k]['m'] > 0 for k in ss), sum(B[k]['m'] > 0 for k in ss)))
print('\nper team (960-band stable, vs tape): wins cand/tape, mean delta')
for c in cands:
    A = R[c]; s = stable(A, [k for k in A if k in T and band(k)])
    by = collections.defaultdict(list)
    for k in s: by[A[k]['team']].append(k)
    print('  %-6s %s' % (c, ' | '.join('%s n%d %d/%d %+.0f' % (t[:10], len(v), sum(A[k]['m'] > 0 for k in v), sum(T[k]['m'] > 0 for k in v), st.mean(A[k]['m'] - T[k]['m'] for k in v))
                                    for t, v in sorted(by.items(), key=lambda kv: -len(kv[1])))))
print('\nall seats: wins (tape %d of %d)' % (sum(r['m'] > 0 for r in T.values()), len(T)))
for c in cands:
    A = R[c]; ks = [k for k in A if k in T]
    out = [k for k in ks if not band(k) and T[k]['m'] > 0 >= A[k]['m']]; out_up = [k for k in ks if not band(k) and A[k]['m'] > 0 >= T[k]['m']]
    inn = [k for k in ks if band(k)]
    print('  %-6s wins %d of %d | in band: %d vs tape %d | outside band: %d vs tape %d, tape W->cand L %d, L->W %d (teams %s)' % (c, sum(A[k]['m'] > 0 for k in ks), len(ks),
          sum(A[k]['m'] > 0 for k in inn), sum(T[k]['m'] > 0 for k in inn), sum(A[k]['m'] > 0 for k in ks if not band(k)), sum(T[k]['m'] > 0 for k in ks if not band(k)),
          len(out), len(out_up), dict(collections.Counter(A[k]['team'][:10] for k in out))))
