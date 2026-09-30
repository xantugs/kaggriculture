"""vcmp.py PANEL : wins / margin of every version on a vgate panel, split by the rival's step-1 class."""
import json, sys, collections, statistics as st
sys.stdout.reconfigure(encoding='utf-8')
panel = sys.argv[1]
V = 'gold/top10/research/versions/'; G = 'gold/top10/gates/'
refs = G + ('lad_v33_refs.jsonl' if panel == 'lad' else 'fresh29_refs.jsonl')
def cls(m, h):
    if h == 0 and 940 <= m <= 980: return 'band'
    for lo, hi in ((540, 720), (2440, 2480)):
        if h == 0 and lo <= m <= hi: return 'C2S3'
    if h == 0 and m >= 2550: return 'chassis'
    if h >= 4 and m < 300: return 'hpoor'
    if (h == 5 and 2200 <= m <= 2500) or (3 <= h <= 5 and 300 <= m <= 1700): return 'hfirst'
    return 'other'
C = {}
for l in open(refs, encoding='utf-8'):
    r = json.loads(l); m = r['money'][1] if len(r['money']) > 1 else -1; h = r['hands'][1] if len(r['hands']) > 1 else -1
    C[(r['gid'], r['seat'])] = cls(m, h)
man = {x['tag']: x for x in json.load(open(V + 'manifest.json'))}
rows = [json.loads(l) for l in open(V + 'vgate_%s.jsonl' % panel, encoding='utf-8')]
by = collections.defaultdict(dict)
for r in rows:
    if r.get('m') is not None: by[r['file'].split('/')[-1][:-3]][(r['gid'], r['seat'])] = r['m']
common = set.intersection(*[set(v) for v in by.values()]) if by else set()
classes = sorted({C[k] for k in common})
print('%s panel: %d games common to all %d versions; classes %s' % (panel, len(common), len(by), dict(collections.Counter(C[k] for k in common))))
print('ver   live-rating | wins  mean margin | ' + ' '.join('%-9s' % c for c in classes) + ' | errors')
for tag in sorted(by):
    ms = [by[tag][k] for k in common]
    per = ' '.join('%-9s' % ('%d/%d' % (sum(by[tag][k] > 0 for k in common if C[k] == c), sum(1 for k in common if C[k] == c))) for c in classes)
    err = sum(1 for r in rows if r['file'].endswith(tag + '.py') and (r.get('m') is None or any(r.get('err') or [])))
    print('%-5s %8s    | %4d  %+9.0f  | %s | %d' % (tag, man.get(tag, {}).get('score', '?'), sum(m > 0 for m in ms), st.mean(ms), per, err))
