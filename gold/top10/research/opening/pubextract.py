"""pubextract.py: static extraction of agent sources from pulled notebooks (../pubnb/*.json): writefile cells, loose cells,
base64/base85 payloads (zlib/gzip/lzma, tar) and big string literals. Writes ../pubnb/x_<slug>.py, scans for unsafe calls,
fingerprints steps 0-1 of the safe ones in a subprocess."""
import sys, os, json, re, base64, zlib, gzip, lzma, tarfile, io, subprocess
KG = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
OUT = os.path.abspath(os.path.join(KG, '..', 'pubnb'))
UNSAFE = re.compile(r'\b(os\.system|subprocess|socket\.|urllib|requests\.|http\.client|shutil\.rmtree|os\.remove|os\.unlink|__import__|ctypes|pty\.|webbrowser)')

def decode_blob(b):
    out = []
    raws = []
    for dec in (lambda x: base64.b85decode(x), lambda x: base64.b64decode(x, validate=False), lambda x: base64.a85decode(x)):
        try:
            raws.append(dec(b))
        except Exception:
            pass
    cands = []
    for raw in raws:
        cands.append(raw)
        for fn in (zlib.decompress, lambda x: gzip.decompress(x), lambda x: zlib.decompress(x, -15), lambda x: lzma.decompress(x)):
            try:
                cands.append(fn(raw))
            except Exception:
                pass
    for data in cands:
        try:
            tf = tarfile.open(fileobj=io.BytesIO(data))
            for m in tf.getmembers():
                if m.isfile() and m.name.endswith('.py'):
                    out.append((m.name, tf.extractfile(m).read().decode('utf-8', 'replace')))
            continue
        except Exception:
            pass
        try:
            t = data.decode('utf-8')
            if 'def agent' in t:
                out.append(('blob.py', t))
        except Exception:
            pass
    return out

def extract(slug):
    d = json.load(open(os.path.join(OUT, slug + '.json'), encoding='utf-8'))
    src = d['blob'].get('source', '')
    if not src.lstrip().startswith('{'):
        return [('script', src)] if 'def agent' in src else []
    nb = json.loads(src); found = []
    for c in nb.get('cells', []):
        if c.get('cell_type') != 'code': continue
        body = c.get('source'); body = ''.join(body) if isinstance(body, list) else (body or '')
        m = re.match(r'\s*%%writefile\s+(-a\s+)?(\S+)\s*\n', body)
        if m and 'def agent' in body:
            found.append(('writefile:' + m.group(2), body[m.end():])); continue
        lits = re.findall(r"'([^'\n]{40,})'|\"([^\"\n]{40,})\"", body)
        parts = [a or b_ for a, b_ in lits]
        joined = ''.join(parts)
        seen = set()
        for blob in ([p_ for p_ in parts if len(p_) >= 20000] + ([joined] if len(joined) >= 20000 else [])):
            if blob[:80] in seen: continue
            seen.add(blob[:80])
            for name, text in decode_blob(re.sub(r'\s+', '', blob)):
                if 'def agent' in text:
                    found.append(('b85:' + name, text))
        for lit in re.findall(r"r?'''(.*?)'''|r?\"\"\"(.*?)\"\"\"", body, re.S):
            t = lit[0] or lit[1]
            if len(t) > 20000 and 'def agent' in t:
                found.append(('literal', t))
        if not m and 'def agent' in body and 'base64' not in body:
            found.append(('cell', '\n'.join(l for l in body.split('\n') if not l.lstrip().startswith(('!', '%')))))
    return found

SIG = r'''
import sys, contextlib, io, json
sys.path.insert(0, %r)
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
A = lean.load(%r)
log = []
def w(obs, cfg=None):
    a = A(obs, cfg)
    st = int(obs['step'])
    if st <= 1 and isinstance(a, dict):
        log.append((st, [o for o in (a.get('market') or []) if isinstance(o, list)]))
    return a
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    r = lean.play(None, None, 7, agent_objs=[w, K.pass_agent], max_steps=3)
print(json.dumps(log))
'''
only = set(sys.argv[1:])
slugs = sorted(f[:-5] for f in os.listdir(OUT) if f.endswith('.json'))
for slug in slugs:
    if only and slug not in only: continue
    try:
        found = extract(slug)
    except Exception as e:
        print('%-52s extract error %s' % (slug[:52], repr(e)[:60])); continue
    if not found:
        print('%-52s no agent found' % slug[:52]); continue
    found.sort(key=lambda x: -len(x[1]))
    how, text = found[0]
    py = os.path.join(OUT, 'x_' + slug + '.py')
    open(py, 'w', encoding='utf-8').write(text)
    bad = sorted(set(UNSAFE.findall(text)))
    if bad:
        print('%-52s %7dB %-18s UNSAFE %s' % (slug[:52], len(text), how[:18], bad[:5])); continue
    try:
        r = subprocess.run([sys.executable, '-c', SIG % (os.path.join(KG, 'arena'), py)], capture_output=True, text=True, timeout=90, cwd=KG)
        out = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
        sig = json.loads(out) if out.startswith('[') else None
        fp = ('ERR ' + (r.stderr.strip().split('\n')[-1][:60] if r.stderr.strip() else 'no output')) if sig is None else \
            ' | '.join('s%d %s' % (st, ' '.join('%s:%s%s' % (o[0][:4], (o[1][:3] if len(o) > 1 and isinstance(o[1], str) else ''), ('x%s' % o[2] if len(o) > 2 else '')) for o in m)) for st, m in sig)
    except subprocess.TimeoutExpired:
        fp = 'TIMEOUT'
    print('%-52s %7dB %-18s %s' % (slug[:52], len(text), how[:18], fp[:140]), flush=True)
