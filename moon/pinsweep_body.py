
# ---- pinned split sweep on games vs 2800+ teams (knob variants and layer bypasses of the base agent) ----
import os, sys, json, zlib, glob, time, statistics as st, collections
W = '/kaggle/working'
sys.path.insert(0, W)
os.environ['PIN_WORKERS'] = str(max(4, (os.cpu_count() or 8) - 4))
blob = sorted(glob.glob('/kaggle/input/**/games2800.bin', recursive=True))[0]
data = json.loads(zlib.decompress(open(blob, 'rb').read()))
os.makedirs(W + '/g', exist_ok=True)
files = []
for d in data['games']:
    fn = W + '/g/%d.json' % d['id']
    json.dump([d], open(fn, 'w', encoding='utf-8')); files.append(fn)
CLS = data['cls']
print('games', len(files), 'workers', os.environ['PIN_WORKERS'], flush=True)
import pinmulti
BASE = W + '/base.py'


def summarize(path, tag):
    by = collections.defaultdict(dict)
    for l in open(path, encoding='utf-8'):
        r = json.loads(l)
        if r['m'] is not None:
            by[r['gid']][r['label']] = r['m']
    labs = sorted({k for d in by.values() for k in d})
    rows = []
    for lab in labs:
        out = {}
        for name, test in (('MIR', lambda s: s >= 0.8), ('DIV', lambda s: s < 0.8)):
            g = [x for x in by if str(x) in CLS and test(CLS[str(x)]) and 'base' in by[x] and lab in by[x]]
            if not g:
                continue
            dd = [by[x][lab] - by[x]['base'] for x in g]
            out[name] = (st.mean(dd), st.pstdev(dd) / len(dd) ** .5, sum(by[x][lab] > 0 for x in g) - sum(by[x]['base'] > 0 for x in g), len(g))
        rows.append((lab, out))
    rows.sort(key=lambda r: -(r[1].get('DIV', (0,))[0] + r[1].get('MIR', (0,))[0]))
    print('==== SUMMARY', tag, flush=True)
    for lab, out in rows:
        m = out.get('MIR', (0, 0, 0, 0)); d = out.get('DIV', (0, 0, 0, 0))
        print(f"{lab:44s} MIR {m[0]:+7.0f} ±{m[1]:4.0f} dW {m[2]:+3d} | DIV {d[0]:+7.0f} ±{d[1]:4.0f} dW {d[2]:+3d}", flush=True)


if __name__ == '__main__':
    t0 = time.time()
    games = [(f, 0) for f in files]
    for tag, variants in PHASES:
        out = W + '/sweep_%s.jsonl' % tag
        vs = [('base', BASE, {})] + [(lab, BASE, g) for lab, g in variants]
        print('phase', tag, 'variants', len(vs), flush=True)
        pinmulti.run(games, S_STEP, vs, out, chunk=CHUNK)
        summarize(out, tag)
        print('elapsed', round(time.time() - t0), flush=True)
