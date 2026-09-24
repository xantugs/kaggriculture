"""Top-tier episode corpus from the official daily datasets (kaggle/kaggriculture-episodes-YYYY-MM-DD).
usage: elite_fetch.py list 2026-09-20 2026-09-22      -> elite/ids_<date>.txt (episode ids = file names)
       elite_fetch.py fetch 2026-09-22 [threads]        -> elite/games_<date>.jsonl (compact, resumable)
Games are fetched gzip-compressed from the public replay endpoint and stored as
{id, info{TeamNames, seed}, rewards, statuses, acts[t] = [seat0 action, seat1 action]} one per line."""
import sys, os, json, time, gzip, datetime, urllib.request
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'elite')
TOKEN = open(os.path.expanduser('~/.kaggle/access_token')).read().strip()
REPLAY = "https://www.kaggle.com/competitions/episodes/%d/replay.json"


def api(url):
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + TOKEN})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def list_day(date):
    ids = []; tok = None
    while True:
        url = "https://www.kaggle.com/api/v1/datasets/list/kaggle/kaggriculture-episodes-%s?pageSize=200" % date
        if tok:
            url += "&pageToken=" + urllib.request.quote(tok)
        d = api(url)
        for f in d.get('datasetFiles') or []:
            n = f.get('name') or ''
            if n.endswith('.json') and n[:-5].isdigit():
                ids.append(int(n[:-5]))
        tok = d.get('nextPageTokenNullable') or d.get('nextPageToken')
        if not tok:
            break
    return ids


def get(eid):
    import subprocess, tempfile
    for attempt in range(3):
        tmp = os.path.join(tempfile.gettempdir(), 'ep_%d.json' % eid)
        try:
            subprocess.run(['curl', '-s', '--compressed', '--max-time', '150', '-A', 'Mozilla/5.0 curl/8.0', '-o', tmp, REPLAY % eid],
                           check=True, timeout=170)
            rep = json.load(open(tmp, encoding='utf-8'))
            acts = [[(x.get('action') if isinstance(x, dict) and isinstance(x.get('action'), dict) else None) for x in s]
                    for s in rep.get('steps') or []]
            info = rep.get('info') or {}
            return dict(id=eid, info=dict(TeamNames=info.get('TeamNames'), seed=info.get('seed'), EpisodeId=eid),
                        rewards=rep.get('rewards'), statuses=rep.get('statuses'), acts=acts)
        except Exception as e:
            err = e; time.sleep(2 + 3 * attempt)
        finally:
            try: os.remove(tmp)
            except OSError: pass
    print('failed', eid, repr(err)[:120], flush=True)
    return None


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    cmd = sys.argv[1]
    if cmd == 'list':
        d0 = datetime.date.fromisoformat(sys.argv[2]); d1 = datetime.date.fromisoformat(sys.argv[3])
        while d0 <= d1:
            ids = list_day(d0.isoformat())
            open(os.path.join(OUT, 'ids_%s.txt' % d0.isoformat()), 'w').write('\n'.join(map(str, ids)))
            print(d0, len(ids), flush=True)
            d0 += datetime.timedelta(days=1)
    elif cmd == 'fetch':
        date = sys.argv[2]; th = int(sys.argv[3]) if len(sys.argv) > 3 else 4
        ids = [int(x) for x in open(os.path.join(OUT, 'ids_%s.txt' % date)).read().split()]
        path = os.path.join(OUT, 'games_%s.jsonl' % date)
        done = set()
        if os.path.exists(path):
            for line in open(path, encoding='utf-8'):
                try: done.add(json.loads(line)['id'])
                except Exception: pass
        todo = [i for i in ids if i not in done]
        print(date, len(todo), 'to fetch', flush=True)
        t0 = time.time(); n = 0
        from concurrent.futures import as_completed
        with ThreadPoolExecutor(th) as ex, open(path, 'a', encoding='utf-8') as fh:
            for fut in as_completed([ex.submit(get, i) for i in todo]):
                rec = fut.result()
                if rec:
                    fh.write(json.dumps(rec, ensure_ascii=False) + '\n'); fh.flush(); n += 1
                    if n % 50 == 0:
                        print(date, n, 'fetched', round(time.time() - t0), 's', flush=True)
        print(date, 'done', n, round(time.time() - t0), 's', flush=True)
