"""Push the evaluation notebook (CPU) with the training kernel output attached. usage: kpush_eval.py script.py [slug] [dataset,dataset]"""
import sys, json, os, urllib.request
tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
slug = sys.argv[2] if len(sys.argv) > 2 else 'kaggriculture-bc-eval'
body = dict(slug='offhand/' + slug, newTitle=slug, text=open(sys.argv[1], encoding='utf-8').read(), language='python', kernelType='script',
            isPrivate=True, enableGpu=False, enableTpu=False, enableInternet=True, datasetDataSources=(sys.argv[3].split(",") if len(sys.argv) > 3 else []), competitionDataSources=[],
            kernelDataSources=['offhand/kaggriculture-bc-train'], modelDataSources=[], categoryIds=[])
req = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/push', data=json.dumps(body).encode(),
                             headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method='POST')
try:
    print(urllib.request.urlopen(req, timeout=180).read().decode()[:300])
except urllib.error.HTTPError as e:
    print('HTTP', e.code, e.read().decode()[:600])
