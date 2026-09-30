"""sentinel.py : one sentinel pass. New live v33 games (live_v33.jsonl ids not yet in gates/sent_refs.jsonl) get refs (rival =
its recorded seat, repaired, in its own town) and are replayed with CGt, c2tr and NMp44Tr. Appends one summary line per pass
plus one line per game to nmloop/sentinel.log, flagging CGt W -> NMp44Tr L and c2tr W -> NMp44Tr L, with the rival's class."""
import sys, os, json, gzip, time
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
import elite_gate
N = 'gold/top10/research/nmloop/'; G = 'gold/top10/gates/'
CANDS = {'CGt': 'gold/final/CGt_final.py', 'c2tr': 'gold/final/c2tr_final.py', 'NMp44Tr': 'gold/final/NMp44Tr_final.py'}


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


if __name__ == '__main__':
    # games already replayed: the lad_v33 gate (first 115) plus every earlier sentinel pass
    done = {json.loads(l)['gid'] for l in open(G + 'lad_v33_refs.jsonl', encoding='utf-8')}
    if os.path.exists(G + 'sent_refs.jsonl'):
        done |= {json.loads(l)['gid'] for l in open(G + 'sent_refs.jsonl', encoding='utf-8') if l.strip()}
    games = [r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{'))
             if r['id'] not in done and all(s == 'DONE' for s in r['statuses'])]
    stamp = time.strftime('%H:%M', time.gmtime())
    if not games:
        open(N + 'sentinel.log', 'a', encoding='utf-8').write('%s pass: no new games\n' % stamp); sys.exit(0)
    with ProcessPoolExecutor(6) as ex:
        refs = [r for r in ex.map(elite_gate._ref, [(g, 1 - g['meta']['seat']) for g in games]) if r]
    gm = {g['id']: g for g in games}
    res = {}
    with ProcessPoolExecutor(6) as ex:
        for c, path in CANDS.items():
            res[c] = {x['gid']: x for x in ex.map(elite_gate._play, [(gm[r['gid']], r, path) for r in refs]) if x.get('m') is not None}
    with open(G + 'sent_refs.jsonl', 'a', encoding='utf-8') as fh:
        for r in refs: fh.write(json.dumps({'gid': r['gid'], 'seat': r['seat'], 'team': r['team']}) + '\n')
    lines = []; nw = {c: 0 for c in CANDS}; flags = 0
    for r in refs:
        g = r['gid']
        if not all(g in res[c] for c in CANDS): continue
        m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
        k = cls(m, h); live = gm[g]['rewards'][gm[g]['meta']['seat']] - gm[g]['rewards'][1 - gm[g]['meta']['seat']]
        ms = {c: res[c][g]['m'] for c in CANDS}
        for c in CANDS: nw[c] += ms[c] > 0
        flag = ''
        if ms['CGt'] > 0 >= ms['NMp44Tr']: flag += ' FLAG:CGt-W/NMp44Tr-L'
        if ms['c2tr'] > 0 >= ms['NMp44Tr']: flag += ' FLAG:c2tr-W/NMp44Tr-L'
        flags += bool(flag)
        lines.append('   %s %-9s %-18s step1 %d/%d live %+7.0f | CGt %+7.0f c2tr %+7.0f NMp44Tr %+7.0f%s' % (g, k, r['team'][:18], m, h, live, ms['CGt'], ms['c2tr'], ms['NMp44Tr'], flag))
    with open(N + 'sentinel.log', 'a', encoding='utf-8') as fh:
        fh.write('%s pass: %d new games | wins CGt %d c2tr %d NMp44Tr %d | flags %d\n' % (stamp, len(lines), nw['CGt'], nw['c2tr'], nw['NMp44Tr'], flags))
        for l in lines: fh.write(l + '\n')
    print('pass done', len(lines), 'games, flags', flags)
