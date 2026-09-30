"""fresh29_cmp.py : held-out check on the 29 Sep top-team gate: TAPE (CGt) vs NMp13 / NMp26 on the 960-band seats (the elite's
step-1 money 940-980 with no hands, from the refs), opponent-stable seats only; plus counts on all seats."""
import json, os, sys, statistics as st, collections
sys.stdout.reconfigure(encoding='utf-8')
N = 'gold/top10/research/nmloop/'; G = 'gold/top10/gates/'
band = {}
for l in open(G + 'fresh29_refs.jsonl', encoding='utf-8'):
    r = json.loads(l); m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
    band[(r['gid'], r['seat'])] = (940 <= m <= 980 and h == 0)
def rows(p):
    if not os.path.exists(p): return {}
    return {(x['gid'], x['seat']): x for x in (json.loads(l) for l in open(p, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None}
T = rows(N + 'f29_TAPE.jsonl')
them = lambda r: r['us'] - r['m']
print('fresh29 seats %d, 960-band %d; tape rows %d' % (len(band), sum(band.values()), len(T)))
for tag in (sys.argv[1:] or ['NMp13', 'NMp26', 'NMp44']):
    A = rows(N + 'f29_%s.jsonl' % tag)
    if not A: print(tag, 'no rows yet'); continue
    ks = [k for k in A if k in T and band.get(k)]
    stb = [k for k in ks if abs(them(A[k]) - them(T[k])) <= 0.2 * max(1, them(T[k]))]
    up = sum(1 for k in stb if A[k]['m'] > 0 and T[k]['m'] <= 0); dn = sum(1 for k in stb if T[k]['m'] > 0 and A[k]['m'] <= 0)
    by = collections.defaultdict(lambda: [0, 0, 0])
    for k in stb: by[A[k]['team']][0] += 1; by[A[k]['team']][1] += A[k]['m'] > 0; by[A[k]['team']][2] += T[k]['m'] > 0
    print('%-6s 960-band stable %d: wins %d vs tape %d (+%d/-%d), margin %+.0f, our cash %+.0f | %s' % (tag, len(stb), sum(A[k]['m'] > 0 for k in stb), sum(T[k]['m'] > 0 for k in stb), up, dn,
          st.mean(A[k]['m'] - T[k]['m'] for k in stb) if stb else float('nan'), st.mean(A[k]['us'] - T[k]['us'] for k in stb) if stb else float('nan'),
          ' '.join('%s %d/%d(n%d)' % (t[:8], a, b, n) for t, (n, a, b) in sorted(by.items(), key=lambda kv: -kv[1][0]))))
