"""Create (or version) a private Kaggle dataset from local files via the public API (no CLI needed).
usage: kdataset.py slug "Title" file1 [file2 ...]"""
import sys, os, json, time, urllib.request
tok = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
H = {'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}


def call(url, body, method='POST', tries=6):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=H, method=method)
            return json.loads(urllib.request.urlopen(req, timeout=300).read() or b'{}')
        except urllib.error.HTTPError as e:
            print('HTTP', e.code, e.read().decode()[:400]); raise
        except Exception as e:
            print('retry', k, repr(e)[:100], flush=True); time.sleep(8 + 8 * k)
    raise RuntimeError(url)


def upload(path):
    n = os.path.getsize(path)
    r = call('https://www.kaggle.com/api/v1/blobs/upload', dict(type='dataset', name=os.path.basename(path), contentLength=n,
                                                                  lastModifiedEpochSeconds=int(os.path.getmtime(path))))
    url, token = r['createUrl'], r['token']
    data = open(path, 'rb').read()
    for k in range(6):
        try:
            req = urllib.request.Request(url, data=data, method='PUT', headers={'Content-Type': 'application/octet-stream'})
            urllib.request.urlopen(req, timeout=600).read(); break
        except Exception as e:
            print('put retry', k, repr(e)[:100], flush=True); time.sleep(8 + 8 * k)
    return token


if __name__ == '__main__':
    slug, title, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    toks = [dict(token=upload(f)) for f in files]
    print('uploaded', len(toks), flush=True)
    body = dict(ownerSlug='offhand', slug=slug, title=title, licenseName='CC0-1.0', isPrivate=True, files=toks,
                subtitle='', description='offhand kaggriculture evaluation games', categories=[])
    try:
        print(call('https://www.kaggle.com/api/v1/datasets/create/new', body))
    except urllib.error.HTTPError:
        print('create failed; trying new version')
        print(call('https://www.kaggle.com/api/v1/datasets/create/version/offhand/%s' % slug,
                   dict(versionNotes='update', files=toks, convertToCsv=False, deleteOldVersions=True)))
