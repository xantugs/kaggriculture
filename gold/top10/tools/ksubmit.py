"""Submit an agent file to Kaggriculture through the Kaggle API (bearer token in ~/.kaggle/access_token).
usage: ksubmit.py file.py "description"          -> prints the new submission id"""
import sys, os, json, time, urllib.request
TOKEN = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
BASE = 'https://www.kaggle.com/api/v1/'


def rpc(name, body):
    req = urllib.request.Request(BASE + 'competitions.CompetitionApiService/' + name, data=json.dumps(body).encode(),
                                 headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read() or b'{}')


if __name__ == '__main__':
    path, desc = sys.argv[1], sys.argv[2]
    raw = open(path, 'rb').read()
    up = rpc('StartSubmissionUpload', {'competitionName': 'kaggriculture', 'contentLength': len(raw),
                                       'lastModifiedEpochSeconds': int(os.path.getmtime(path)), 'fileName': os.path.basename(path)})
    print('upload slot', {k: (v[:40] + '...' if isinstance(v, str) and len(v) > 40 else v) for k, v in up.items()})
    put = urllib.request.Request(up['createUrl'], data=raw, method='PUT', headers={'Content-Type': 'application/octet-stream'})
    with urllib.request.urlopen(put, timeout=300) as r:
        print('uploaded', r.status)
    res = rpc('CreateSubmission', {'competitionName': 'kaggriculture', 'blobFileTokens': up['token'], 'submissionDescription': desc})
    print(json.dumps(res))
