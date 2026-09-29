"""pub_refresh.py REF [REF ...] : pull the LATEST version of each public notebook into ../pubnb/v930/, extract its agent
(pubextract logic), skip unsafe sources (network/subprocess/ctypes/...), fingerprint steps 0-1 of the safe ones in a
subprocess, and flag the new egg/wheat meta opening (step 0 = BUY_PRODUCT WHEAT 5 + COW 1 + 3 x SHEEP 1)."""
import sys, os, json, time, urllib.request, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pubextract as PE
NEWDIR = os.path.join(PE.OUT, 'v930'); os.makedirs(NEWDIR, exist_ok=True)
PE.OUT = NEWDIR
TOK = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
TARGET0 = sorted([('BUY_PRODUCT', 'WHEAT', 5), ('BUY_ANIMAL', 'COW', 1), ('BUY_ANIMAL', 'SHEEP', 1), ('BUY_ANIMAL', 'SHEEP', 1), ('BUY_ANIMAL', 'SHEEP', 1)])
for ref in sys.argv[1:]:
    u, s = ref.split('/')
    f = os.path.join(NEWDIR, s + '.json')
    if not os.path.exists(f):
        req = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/pull?userName=%s&kernelSlug=%s' % (u, s), headers={'Authorization': 'Bearer ' + TOK})
        try:
            open(f, 'wb').write(urllib.request.urlopen(req, timeout=120).read())
        except Exception as e:
            print(json.dumps(dict(ref=ref, status='pull failed ' + repr(e)[:60]))); continue
    meta = json.load(open(f, encoding='utf-8')).get('metadata', {})
    try:
        found = PE.extract(s)
    except Exception as e:
        print(json.dumps(dict(ref=ref, status='extract error ' + repr(e)[:60]))); continue
    if not found:
        print(json.dumps(dict(ref=ref, status='no agent'))); continue
    found.sort(key=lambda x: -len(x[1])); how, text = found[0]
    py = os.path.join(NEWDIR, 'x_' + s + '.py'); open(py, 'w', encoding='utf-8').write(text)
    bad = sorted(set(PE.UNSAFE.findall(text)))
    if bad:
        print(json.dumps(dict(ref=ref, status='unsafe', bad=bad, size=len(text)))); continue
    try:
        r = subprocess.run([sys.executable, '-c', PE.SIG % (os.path.join(PE.KG, 'arena'), py)], capture_output=True, text=True, timeout=120, cwd=PE.KG)
        out = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
        sig = json.loads(out) if out.startswith('[') else 'ERR ' + (r.stderr.strip().split('\n')[-1][:80] if r.stderr.strip() else 'no output')
    except subprocess.TimeoutExpired:
        sig = 'TIMEOUT'
    s0 = sorted(tuple(o) for st, m in sig if st == 0 for o in m if o != ['PASS']) if isinstance(sig, list) else None
    print(json.dumps(dict(ref=ref, status='ok', size=len(text), version=meta.get('versionNumber') or meta.get('currentVersionNumber'),
                          newmeta=(s0 == TARGET0), s0=s0, s1=[o for st, m in sig if st == 1 for o in m][:8] if isinstance(sig, list) else sig), ensure_ascii=False))
