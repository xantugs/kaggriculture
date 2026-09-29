"""pubsweep.py: pull every not-yet-pulled competition notebook (../pubnb/_all_refs.json), extract its agent (pubextract logic),
fingerprint steps 0-1 with 4 workers; write ../pubnb/_sweep.jsonl (one row per notebook) and flag C2S3 lineage signatures."""
import sys, os, json, re, subprocess, urllib.request, time
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pubextract as PE
KG = PE.KG; OUT = PE.OUT
TOK = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
refs = json.load(open(os.path.join(OUT, '_all_refs.json')))
def pull(ref):
    u, s = ref.split('/')
    f = os.path.join(OUT, s + '.json')
    if os.path.exists(f): return s
    req = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/pull?userName=%s&kernelSlug=%s' % (u, s), headers={'Authorization': 'Bearer ' + TOK})
    for k in range(3):
        try:
            data = urllib.request.urlopen(req, timeout=120).read(); open(f, 'wb').write(data); return s
        except Exception as e:
            time.sleep(3 + 3 * k)
    return None
def fp(py):
    try:
        r = subprocess.run([sys.executable, '-c', PE.SIG % (os.path.join(KG, 'arena'), py)], capture_output=True, text=True, timeout=120, cwd=KG)
        out = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
        return json.loads(out) if out.startswith('[') else 'ERR ' + (r.stderr.strip().split('\n')[-1][:80] if r.stderr.strip() else 'no output')
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
def work(ref):
    s = pull(ref)
    if s is None: return dict(ref=ref, status='pull failed')
    try:
        found = PE.extract(s)
    except Exception as e:
        return dict(ref=ref, status='extract error ' + repr(e)[:60])
    if not found: return dict(ref=ref, status='no agent')
    found.sort(key=lambda x: -len(x[1])); how, text = found[0]
    py = os.path.join(OUT, 'x_' + s + '.py'); open(py, 'w', encoding='utf-8').write(text)
    bad = sorted(set(PE.UNSAFE.findall(text)))
    if bad: return dict(ref=ref, status='unsafe', bad=bad, size=len(text), how=how)
    sig = fp(py)
    row = dict(ref=ref, status='ok', size=len(text), how=how, sig=sig)
    if isinstance(sig, list):
        s0 = [o for st, m in sig if st == 0 for o in m]; s1 = [o for st, m in sig if st == 1 for o in m]
        c2s3 = any(o[0] == 'BUY_ANIMAL' and o[1] == 'COW' for o in s0) and any(o[0] == 'BUY_PRODUCT' and o[1] == 'WHEAT' for o in s0) and any(o[0] == 'BUY_ANIMAL' and o[1] == 'SHEEP' and int(o[2]) == 3 for o in s1)
        row['c2s3'] = bool(c2s3)
    return row
rows = []
with ThreadPoolExecutor(4) as ex, open(os.path.join(OUT, '_sweep.jsonl'), 'w', encoding='utf-8') as fh:
    for row in ex.map(work, refs):
        rows.append(row); fh.write(json.dumps(row) + '\n'); fh.flush()
        if row.get('c2s3'): print('C2S3 LINEAGE:', row['ref'], row.get('sig'), flush=True)
import collections
print('done', len(rows), dict(collections.Counter(r['status'] for r in rows)))
print('c2s3 hits:', [r['ref'] for r in rows if r.get('c2s3')])
