"""Keep Kaggle kernel slots busy and collect results.
usage: kqueue.py state.json [poll_seconds]
state.json = {"running": [slug, ...], "pending": [[slug, script, "cpu"|"tpu"], ...], "done": [slug, ...]}
Polls every running kernel; a finished one (complete / error / cancelled) has its output files downloaded to
gold/top10/gates/kout/<slug>/ and moves to "done"; free CPU slots (max 5 batch CPU sessions) take pending kernels.
Exits after at least one kernel finished (so the caller is notified), printing what finished."""
import sys, os, json, time, urllib.request, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
TOK = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
DS = 'offhand/kagg-gates-0927,offhand/kagg-opps-0927,offhand/kagg-bases-0927'
MAX_CPU = 5


def get(url):
    for k in range(5):
        try:
            req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + TOK})
            return urllib.request.urlopen(req, timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            err = e
        except Exception as e:
            err = e
        time.sleep(5 + 5 * k)
    print('get failed', url[:90], repr(err)[:100], flush=True)
    return None


def status(slug):
    b = get('https://www.kaggle.com/api/v1/kernels/status?userName=offhand&kernelSlug=%s' % slug)
    return json.loads(b).get('status') if b else None


def download(slug):
    b = get('https://www.kaggle.com/api/v1/kernels/output?userName=offhand&kernelSlug=%s' % slug)
    if not b:
        return []
    d = json.loads(b); out = os.path.join(ROOT, 'gold', 'top10', 'gates', 'kout', slug); os.makedirs(out, exist_ok=True)
    got = []
    for f in d.get('files') or []:
        name = f.get('fileName') or f.get('fileNameNullable'); url = f.get('url') or f.get('urlNullable')
        if not name or '/' in name or not (name.endswith('.jsonl') or name.endswith('.txt')):
            continue
        data = get(url)
        if data is not None:
            open(os.path.join(out, name), 'wb').write(data); got.append(name)
    log = d.get('log') or d.get('logNullable') or ''
    try:
        log = ''.join(x.get('data', '') for x in json.loads(log))
    except Exception:
        pass
    open(os.path.join(out, 'kernel.log'), 'w', encoding='utf-8').write(str(log))
    return got


def push(slug, script, kind):
    r = subprocess.run([sys.executable, os.path.join(ROOT, 'moon', 'kpush_tpu.py'), script, slug, kind, DS],
                       capture_output=True, text=True, timeout=600)
    ok = '"versionNumber' in r.stdout and 'errorNullable' not in r.stdout
    print('push', slug, kind, 'ok' if ok else r.stdout[-200:], flush=True)
    return ok


if __name__ == '__main__':
    path = sys.argv[1]; poll = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    finished = []
    inbox = os.path.join(os.path.dirname(os.path.abspath(path)), 'kinbox.txt')  # append "slug script cpu|tpu" lines here
    while True:
        st = json.load(open(path, encoding='utf-8'))
        if os.path.exists(inbox):
            lines = [l.split() for l in open(inbox, encoding='utf-8') if l.strip()]
            open(inbox, 'w').close()
            for l in lines:
                if len(l) == 3 and l[0] not in st['running'] + st['done'] and l not in st['pending']:
                    st['pending'].append(l); print('queued', l[0], flush=True)
        for slug in list(st['running']):
            s = status(slug)
            if s in ('complete', 'error', 'cancelAcknowledged', 'cancelled'):
                files = download(slug)
                st['running'].remove(slug); st['done'].append(slug); finished.append((slug, s, files))
                print('finished', slug, s, files, flush=True)
        n_cpu = sum(1 for s in st['running'] if not s.endswith('-tpu') and s != 'kagg-gate-r1')
        while st['pending'] and n_cpu < MAX_CPU:
            slug, script, kind = st['pending'][0]
            if not push(slug, os.path.join(ROOT, script), kind):
                break
            st['pending'].pop(0); st['running'].append(slug); n_cpu += 1
        json.dump(st, open(path, 'w', encoding='utf-8'), indent=1)
        if finished:
            for slug, s, files in finished:
                print('DONE', slug, s, files)
            break
        if not st['running'] and not st['pending']:
            print('nothing running or pending'); break
        time.sleep(poll)
