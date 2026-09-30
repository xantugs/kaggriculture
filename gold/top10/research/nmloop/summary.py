"""summary.py TAG [TAG ...] : compact results of candidates vs the tape (CGt / c2tr) for the ChatGPT loop."""
import json, os, sys, statistics as st, collections
sys.stdout.reconfigure(encoding='utf-8')
N = 'gold/top10/research/nmloop/'; D = 'gold/top10/research/v33loss/'; O = 'gold/top10/research/opening/fresh28/'
live = {r['id']: r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{'))}
NMG = [115333932, 115335380, 115338309, 115336805, 115345249, 115332494]   # the six 960-band ladder games (5 losses + azamat win)
def rows(p, key):
    if not os.path.exists(p): return {}
    return {key(x): x for x in (json.loads(l) for l in open(p, encoding='utf-8') if l.startswith('{')) if x.get('m') is not None}
tape_lg = rows(D + 'lg_CGt.jsonl', lambda x: x['gid'])
tape_f = rows(O + 'c2tr.jsonl', lambda x: (x['gid'], x['seat']))
tape_bl = {lab: [json.loads(l) for l in open(N + 'bl_TAPE160_%s.jsonl' % lab)] for lab in ('RSTurley', 'SiyuanWang', 'YandG', 'pangzi233')}
them = lambda r: r['us'] - r['m']
print('tape baseline: ladder %s | blind %d/160' % (' '.join('%+.1fk' % (tape_lg[g]['m'] / 1000) for g in NMG), sum(r['m'] > 0 for v in tape_bl.values() for r in v)))
for tag in sys.argv[1:]:
    lg = rows(N + 'lg_%s.jsonl' % tag, lambda x: x['gid']) or rows(D + 'lg_%s.jsonl' % tag, lambda x: x['gid'])
    fl = sum(1 for g in NMG if g in lg and lg[g]['m'] > 0 and tape_lg[g]['m'] <= 0); bad = sum(1 for g in NMG if g in lg and lg[g]['m'] <= 0 and tape_lg[g]['m'] > 0)
    bl = []
    for lab in tape_bl:
        p = N + 'bl_%s_%s.jsonl' % (tag, lab)
        if os.path.exists(p): bl += [json.loads(l) for l in open(p)]
    f = rows(N + 'f960_%s.jsonl' % tag, lambda x: (x['gid'], x['seat']))
    ks = [k for k in f if k in tape_f]
    stb = [k for k in ks if abs(them(f[k]) - them(tape_f[k])) <= 0.2 * max(1, them(tape_f[k]))]
    up = sum(1 for k in stb if f[k]['m'] > 0 and tape_f[k]['m'] <= 0); dn = sum(1 for k in stb if tape_f[k]['m'] > 0 and f[k]['m'] <= 0)
    dcash = st.mean(f[k]['us'] - tape_f[k]['us'] for k in stb) if stb else float('nan')
    dm = st.mean(f[k]['m'] - tape_f[k]['m'] for k in stb) if stb else float('nan')
    err = sum(1 for k in ks if any(f[k].get('err') or [])) + sum(1 for g in lg if any(lg[g].get('err') or []))
    by = collections.defaultdict(lambda: [0, 0, 0])
    for k in stb: t = f[k]['team']; by[t][0] += 1; by[t][1] += f[k]['m'] > 0; by[t][2] += tape_f[k]['m'] > 0
    print('%-8s ladder %s | flips +%d/-%d | blind %d/%d (%+.1fk) | fresh960 %d seats: wins %d vs tape %d, +%d/-%d, margin %+.0f, cash %+.0f | err %d | teams %s' % (
        tag, ' '.join('%+.1fk' % (lg[g]['m'] / 1000) if g in lg else '  -  ' for g in NMG), fl, bad, sum(r['m'] > 0 for r in bl), len(bl),
        (st.mean(r['m'] for r in bl) / 1000) if bl else float('nan'), len(stb), sum(f[k]['m'] > 0 for k in stb), sum(tape_f[k]['m'] > 0 for k in stb), up, dn,
        dm, dcash, err, ' '.join('%s %d/%d' % (t[:6], a, b) for t, (n, a, b) in sorted(by.items(), key=lambda kv: -kv[1][0]) if n >= 10)))
