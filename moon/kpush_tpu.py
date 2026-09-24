"""Push a script kernel. usage: kpush_tpu.py script.py slug [tpu|cpu]"""
import sys, json, os, urllib.request
tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
tpu = (sys.argv[3] if len(sys.argv) > 3 else 'tpu') == 'tpu'
body = dict(slug='offhand/' + sys.argv[2], newTitle=sys.argv[2], text=open(sys.argv[1], encoding='utf-8').read(), language='python', kernelType='script',
            isPrivate=True, enableGpu=False, enableTpu=tpu, enableInternet=True, datasetDataSources=(sys.argv[4].split(',') if len(sys.argv) > 4 else []), competitionDataSources=[],
            kernelDataSources=[], modelDataSources=[], categoryIds=[])
req = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/push', data=json.dumps(body).encode(),
                             headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method='POST')
import time
for k in range(6):
    try:
        req = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/push', data=json.dumps(body).encode(),
                                     headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method='POST')
        print(urllib.request.urlopen(req, timeout=180).read().decode()[:300]); break
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, e.read().decode()[:600]); break
    except Exception as e:
        print('retry', k, repr(e)[:100], flush=True); time.sleep(8 + 8 * k)
