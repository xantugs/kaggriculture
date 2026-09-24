"""Push a script kernel to Kaggle. usage: kpush.py script.py slug [dataset,dataset,...]"""
import sys, json, os, urllib.request
tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
script, slug = sys.argv[1], sys.argv[2]
ds = sys.argv[3].split(',') if len(sys.argv) > 3 else ['kaggle/kaggriculture-episodes-2026-09-20', 'kaggle/kaggriculture-episodes-2026-09-21', 'kaggle/kaggriculture-episodes-2026-09-22']
body = dict(slug='offhand/' + slug, newTitle=slug, text=open(script, encoding='utf-8').read(), language='python', kernelType='script',
            isPrivate=True, enableGpu=True, enableTpu=False, enableInternet=True, datasetDataSources=ds,
            competitionDataSources=[], kernelDataSources=(sys.argv[4].split(',') if len(sys.argv) > 4 and sys.argv[4] else []), modelDataSources=[], categoryIds=[])
req = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/push', data=json.dumps(body).encode(),
                             headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method='POST')
try:
    print(urllib.request.urlopen(req, timeout=120).read().decode()[:400])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:600])
