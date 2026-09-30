"""lad_cmp.py : the 115 live v33 games as a gate (rival = its recorded seat, repaired, in its own town): wins of the tape (CGt),
c2tr (= live v33's code) and NMp44T, flips vs c2tr, by rival class; and how well the c2tr replay tracks the live result."""
import json, collections, statistics as st, sys
sys.stdout.reconfigure(encoding='utf-8')
N = 'gold/top10/research/nmloop/'; G = 'gold/top10/gates/'
def cls(m, h):
    if h == 0 and 940 <= m <= 980: return 'C2S3nm'
    for lo, hi in ((540, 720), (2440, 2480)):
        if h == 0 and lo <= m <= hi: return 'C2S3'
    if h == 0 and m >= 2550: return 'chassis'
    if h >= 4 and m < 300: return 'herdpoor'
    if h == 5 and 2200 <= m <= 2500: return 'herdfirst'
    if h == 5 and 1700 < m < 2200: return 'majkel'
    if 3 <= h <= 5 and 300 <= m <= 1700: return 'herdfirst'
    return 'other'
refs = {}
for l in open(G + 'lad_v33_refs.jsonl', encoding='utf-8'):
    r = json.loads(l); m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
    refs[(r['gid'], r['seat'])] = (cls(m, h), r['team'])
live = {}
for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8'):
    if l.startswith('{'):
        g = json.loads(l); s = g['meta']['seat']; live[g['id']] = g['rewards'][s] - g['rewards'][1 - s]
def rows(p): return {(x['gid'], x['seat']): x for x in (json.loads(l) for l in open(p, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None}
C = {c: rows(N + 'lad_%s.jsonl' % c) for c in ('TAPE', 'c2tr', 'NMp44T')}
ks = [k for k in refs if all(k in C[c] for c in C)]
print('games %d; live v33 wins %d' % (len(ks), sum(live[k[0]] > 0 for k in ks)))
for c in C:
    print('  %-7s wins %3d | mean margin %+7.0f' % (c, sum(C[c][k]['m'] > 0 for k in ks), st.mean(C[c][k]['m'] for k in ks)))
agree = sum(1 for k in ks if (C['c2tr'][k]['m'] > 0) == (live[k[0]] > 0))
print('c2tr replay agrees with the live outcome in %d of %d games' % (agree, len(ks)))
by = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
for k in ks:
    c = refs[k][0]; v = by[c]; v[0] += 1; v[1] += live[k[0]] > 0; v[2] += C['TAPE'][k]['m'] > 0; v[3] += C['c2tr'][k]['m'] > 0; v[4] += C['NMp44T'][k]['m'] > 0
print('by class: n / live / tape / c2tr / NMp44T')
for c, v in sorted(by.items(), key=lambda kv: -kv[1][0]):
    print('  %-9s %3d | %3d %3d %3d %3d' % (c, *v))
print('flips NMp44T vs c2tr:')
for k in ks:
    a, b = C['c2tr'][k]['m'], C['NMp44T'][k]['m']
    if (a > 0) != (b > 0): print('  %s %-9s %-20s live %+7.0f c2tr %+7.0f NMp44T %+7.0f tape %+7.0f' % (k, refs[k][0], refs[k][1][:20], live[k[0]], a, b, C['TAPE'][k]['m']))
