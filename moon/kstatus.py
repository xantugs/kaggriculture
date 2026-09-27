"""Kaggle kernel status / log tail / output download. usage: kstatus.py status|log|output [slug]"""
import sys, os, json, urllib.request
tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
slug = sys.argv[2] if len(sys.argv) > 2 else 'kaggriculture-il-train'
def get(url):
    import time
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:
            err = e; time.sleep(5 + 5 * attempt)
    raise err
cmd = sys.argv[1]
if cmd == 'status':
    print(get('https://www.kaggle.com/api/v1/kernels/status?userName=offhand&kernelSlug=%s' % slug).decode()[:500])
elif cmd in ('log', 'output'):
    d = json.loads(get('https://www.kaggle.com/api/v1/kernels/output?userName=offhand&kernelSlug=%s' % slug))
    if cmd == 'log':
        log = d.get('log') or d.get('logNullable') or ''
        try:
            lines = [x.get('data', '') for x in json.loads(log)]
            print(''.join(lines)[-3000:])
        except Exception:
            print(str(log)[-3000:])
    else:
        os.makedirs('kout', exist_ok=True)
        for f in d.get('files') or []:
            name = f.get('fileName') or f.get('fileNameNullable'); url = f.get('url') or f.get('urlNullable')
            if '/' in name or not (name.endswith('.jsonl') or name.endswith('.txt') or name.endswith('.json')): continue
            data = get(url); open(os.path.join('kout', name), 'wb').write(data); print('saved', name, len(data))
