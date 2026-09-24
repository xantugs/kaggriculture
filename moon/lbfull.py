import json, os, urllib.request, zipfile, io, csv, sys
tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
def get(url, timeout=60):
    for k in range(3):
        try:
            req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok})
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:
            err = e
    raise err
try:
    raw = get('https://www.kaggle.com/api/v1/competitions/kaggriculture/leaderboard/download', 120)
    z = zipfile.ZipFile(io.BytesIO(raw)); name = z.namelist()[0]
    rows = list(csv.DictReader(io.TextIOWrapper(z.open(name), encoding='utf-8')))
    print('rows', len(rows), 'cols', list(rows[0].keys()))
    for i, r in enumerate(rows):
        if r.get('TeamName') == 'offhand': print('offhand rank', i + 1, r)
    for k in (10, 20, 29, 30, 40, 50, 100): print('rank', k, rows[k - 1].get('TeamName'), rows[k - 1].get('Score'))
except Exception as e:
    print('download failed', repr(e)[:200])
try:
    d = json.loads(get('https://www.kaggle.com/api/v1/competitions/submissions/list/kaggriculture?page=1'))
    for s in d[:8]: print(s.get('ref'), s.get('date'), s.get('status'), s.get('publicScore'), (s.get('description') or '')[:50])
except Exception as e:
    print('subs failed', repr(e)[:200])
