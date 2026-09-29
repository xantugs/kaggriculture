"""fresh_analysis.py : FWt / T8fcWt / CGt (/ c2tr) on the fresh elite gate (fresh28: 851 seats of top-45 teams, 27-28 Sep
daily datasets), for ChatGPT's round: (1) copy band: how many elite seats the step-2 cash rule calls a copy; (2) wins, flips
and margins per agent on opponent-stable seats, overall, by day (27 vs 28) and by team; (3) CGt identity vs T8fcWt on every
divergent seat; (4) town regimes at day 6 / day 9 (yarn count, strawberry shops, bakery/brunch, total, first shops) with T8
loss rate, margin and product ledger, and the same tables on each day separately (discover on one, check on the other)."""
import json, os, sys, collections, statistics as st
sys.stdout.reconfigure(encoding='utf-8')
O = 'gold/top10/research/opening/'
G = 'gold/top10/gates/'


def rows(p):
    d = {}
    if not os.path.exists(p): return d
    for l in open(p, encoding='utf-8'):
        if l.startswith('{'):
            x = json.loads(l)
            if x.get('m') is not None: d[(x['gid'], x['seat'])] = x
    return d


ref = {}
for l in open(G + 'fresh28_refs.jsonl', encoding='utf-8'):
    r = json.loads(l); ref[(r['gid'], r['seat'])] = r
ids27 = set(int(x) for x in open('moon/elite/ids_2026-09-27.txt').read().split())
day = {k: ('27' if k[0] in ids27 else '28') for k in ref}
R = {a: rows(O + 'fresh28/%s.jsonl' % a) for a in ('FWt', 'T8fcWt', 'CGt', 'c2tr')}
R = {a: v for a, v in R.items() if v}
A, B = R['FWt'], R['T8fcWt']
t = lambda r, k: (r.get('tel') or {}).get(k, 0) or 0
them = lambda r: r['us'] - r['m']
ks = [k for k in B if all(k in R[a] for a in R)]
stable = [k for k in ks if all(abs(them(R[a][k]) - them(B[k])) <= 0.2 * max(1, them(B[k])) for a in R)]
print('fresh28: %d seats with all of %s; opponent-stable %d' % (len(ks), '/'.join(R), len(stable)))

print('\n(1) COPY BAND (gc_div2 == 0 means the step-2 cash rule called the elite a chassis copy):')
cp = [k for k in ks if not t(A[k], 'gc_div2')]
print('   copy seats %d of %d; by team: %s' % (len(cp), len(ks), dict(collections.Counter(A[k]['team'] for k in cp))))
print('   step-2 rival money of copy seats:', sorted(t(A[k], 'gc_div2_money') for k in cp)[:30])

print('\n(2) WINS on stable seats (all / day 27 / day 28), paired flips vs T8fcWt, margins')
for a in R:
    w = lambda K: sum(R[a][k]['m'] > 0 for k in K)
    s27 = [k for k in stable if day[k] == '27']; s28 = [k for k in stable if day[k] == '28']
    up = sum(1 for k in stable if R[a][k]['m'] > 0 and B[k]['m'] <= 0); dn = sum(1 for k in stable if B[k]['m'] > 0 and R[a][k]['m'] <= 0)
    d = [R[a][k]['m'] - B[k]['m'] for k in stable]
    print('   %-7s wins %3d of %d (%.1f%%) | d27 %3d/%d d28 %3d/%d | vs T8fcWt only-wins %2d / %2d | margin diff %+5.0f +- %4.0f' % (
        a, w(stable), len(stable), 100 * w(stable) / len(stable), w(s27), len(s27), w(s28), len(s28), up, dn, st.mean(d), st.pstdev(d) / len(d) ** 0.5))
print('   by team (wins FWt / T8fcWt%s):' % (' / CGt' if 'CGt' in R else ''))
bt = collections.defaultdict(list)
for k in stable: bt[A[k]['team']].append(k)
for tm, K in sorted(bt.items(), key=lambda kv: -len(kv[1])):
    print('      %-24s n %3d  %s  | FW-only %d T8-only %d' % (tm[:24], len(K), ' / '.join(str(sum(R[a][k]['m'] > 0 for k in K)) for a in ('FWt', 'T8fcWt', 'CGt') if a in R),
          sum(1 for k in K if A[k]['m'] > 0 and B[k]['m'] <= 0), sum(1 for k in K if B[k]['m'] > 0 and A[k]['m'] <= 0)))

if 'CGt' in R:
    Cg = R['CGt']
    dv = [k for k in ks if t(A[k], 'gc_div2')]
    same = sum(1 for k in dv if Cg[k]['us'] == B[k]['us'] and Cg[k]['m'] == B[k]['m'])
    print('\n(3) CGt IDENTITY: divergent seats %d, CGt == T8fcWt (cash and margin) on %d; copy seats %d, CGt == FWt on %d' % (
        len(dv), same, len(cp), sum(1 for k in cp if Cg[k]['us'] == A[k]['us'] and Cg[k]['m'] == A[k]['m'])))
    for k in [k for k in dv if not (Cg[k]['us'] == B[k]['us'] and Cg[k]['m'] == B[k]['m'])][:8]:
        print('      differs', k, B[k]['us'], B[k]['m'], '->', Cg[k]['us'], Cg[k]['m'])

print('\n(4) TOWN REGIMES (T8fcWt on stable seats; shops unlock at days 3, 6, 9, ...; "by d6" = first 2 shops, "by d9" = first 3)')
S_STRAW = ('BRUNCH_SPOT', 'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP', 'FARMERS_MARKET'); S_EW = ('BAKERY', 'BRUNCH_SPOT')
feats = {
    'final yarn': lambda s: min(s.count('YARN_STORE'), 2),
    'yarn by d9': lambda s: min(s[:3].count('YARN_STORE'), 1),
    'yarn by d6': lambda s: min(s[:2].count('YARN_STORE'), 1),
    'straw shops by d6': lambda s: sum(1 for x in s[:2] if x in S_STRAW),
    'egg/wheat (bakery/brunch) by d9': lambda s: min(sum(1 for x in s[:3] if x in S_EW), 2),
    'no yarn & >=1 bakery/brunch by d9': lambda s: int(s[:3].count('YARN_STORE') == 0 and sum(1 for x in s[:3] if x in S_EW) >= 1),
    'first shop': lambda s: s[0] if s else '-',
}
for name, f in feats.items():
    print('   %s:' % name)
    by = collections.defaultdict(list)
    for k in stable: by[f(ref[k]['shops'])].append(k)
    for v, K in sorted(by.items(), key=lambda kv: str(kv[0])):
        K27 = [k for k in K if day[k] == '27']; K28 = [k for k in K if day[k] == '28']
        wr = lambda KK: '%3.0f%%' % (100 * sum(B[k]['m'] > 0 for k in KK) / len(KK)) if KK else '  - '
        print('      %-18s n %3d  T8 win %s (d27 %s n%3d, d28 %s n%3d)  margin %+6.0f  FWt win %s' % (
            str(v)[:18], len(K), wr(K), wr(K27), len(K27), wr(K28), len(K28), st.mean(B[k]['m'] for k in K), wr([k for k in K if k in A]) if False else '%3.0f%%' % (100 * sum(A[k]['m'] > 0 for k in K) / len(K))))
print('\n   ledger gap (T8fcWt us - elite) by final yarn count:')
for c in (0, 1, 2):
    K = [k for k in stable if min(ref[k]['shops'].count('YARN_STORE'), 2) == c]
    items = sorted({p for k in K for p in list(B[k].get('led_us') or {}) + list(B[k].get('led_elite') or {})})
    print('      yarn %d%s n %3d: %s' % (c, '+' if c == 2 else '', len(K), ', '.join('%s %+.0f' % (p, st.mean((B[k].get('led_us') or {}).get(p, 0) - (B[k].get('led_elite') or {}).get(p, 0) for k in K)) for p in items)))
