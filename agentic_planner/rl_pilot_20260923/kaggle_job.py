"""Private experiment API client. Never prints credentials or signed file URLs."""
from pathlib import Path
import json
import sys
import time
import http.client
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
USER = 'offhand'
DEFAULT_SLUG = 'kaggriculture-codex-rl-pilot-0923'


def api(endpoint, body=None):
    token = Path.home().joinpath('.kaggle/access_token').read_text().strip()
    request = urllib.request.Request('https://www.kaggle.com/api/v1/kernels/' + endpoint,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    for attempt in range(1 if body is not None else 3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except (http.client.RemoteDisconnected, TimeoutError, urllib.error.URLError):
            if body is not None or attempt == 2:
                raise
            time.sleep(2)


def main():
    command = sys.argv[1]
    slug = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SLUG
    assert all(c.isalnum() or c == '-' for c in slug)
    query = urllib.parse.urlencode(dict(userName=USER, kernelSlug=slug))
    if command == 'push':
        source = HERE / (sys.argv[3] if len(sys.argv) > 3 else 'pilot.py')
        result = api('push', dict(slug=USER+'/'+slug, newTitle=slug, text=source.read_text(encoding='utf-8'),
            language='python', kernelType='script', isPrivate=True, enableGpu=False, enableTpu=False,
            enableInternet=True, datasetDataSources=[], competitionDataSources=[],
            kernelDataSources=['offhand/kaggriculture-bc-train'], modelDataSources=[], categoryIds=[]))
        print(json.dumps({k:result.get(k) for k in ['ref','url','versionNumber','error','hasError']}, ensure_ascii=True))
        (HERE / ('push_' + slug + '.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
    elif command == 'status':
        d = api('status?' + query)
        print(json.dumps({k:d.get(k) for k in ['status','failureMessage','hasFailureMessage']}, ensure_ascii=True))
    elif command in ('log', 'fetch', 'progress'):
        d = api('output?' + query)
        log = d.get('log') or d.get('logNullable') or ''
        try:
            text = ''.join(x.get('data','') for x in json.loads(log))
        except (TypeError, ValueError):
            text = str(log)
        destination = HERE / 'outputs' / slug
        destination.mkdir(parents=True, exist_ok=True)
        (destination / 'run.log').write_text(text, encoding='utf-8')
        if command == 'progress':
            lines = [line for line in text.splitlines() if line.startswith(('EVAL ', 'WARM', 'PARITY ', 'ITER ', 'FINAL ', 'Traceback', 'AssertionError', 'RuntimeError', 'cpus ', 'init '))]
            print('\n'.join(lines[-8:]) if lines else 'No training progress published yet.')
        else:
            print(text[-6500:])
        if command == 'fetch':
            allowed = {'summary.json', 'evaluations.json', 'rl_history.json', 'source_manifest.json',
                       'best_model.npz', 'warm_model.npz', 'initial_model.npz', 'last_model.npz', 'bc_model.npz'}
            for f in d.get('files') or []:
                name = f.get('fileName') or f.get('fileNameNullable')
                if name not in allowed:
                    continue
                url = f.get('url') or f.get('urlNullable')
                assert urllib.parse.urlparse(url).scheme == 'https'
                # Signed download links use their own authorization, never the API token.
                with urllib.request.urlopen(url, timeout=90) as response:
                    data = response.read()
                (destination / name).write_bytes(data)
                print('saved', name, len(data))
    else:
        raise ValueError(command)


if __name__ == '__main__':
    try:
        main()
    except urllib.error.HTTPError as e:
        print('HTTP', e.code)
        sys.exit(1)
