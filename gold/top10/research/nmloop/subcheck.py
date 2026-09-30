"""subcheck.py : status and score of our latest submissions (read-only Kaggle API)."""
import os, json, urllib.request
TOKEN = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
req = urllib.request.Request('https://www.kaggle.com/api/v1/competitions/submissions/list/kaggriculture?page=1', headers={'Authorization': 'Bearer ' + TOKEN})
d = json.loads(urllib.request.urlopen(req, timeout=60).read())
subs = d if isinstance(d, list) else d.get('submissions', d)
for s in subs[:4]:
    print(s.get('ref') or s.get('id'), (s.get('date') or '')[:19], (s.get('description') or '')[:28], '| status', s.get('status'), '| score', s.get('publicScore'), '| error', (s.get('errorDescription') or '')[:80])
