"""Download public episode replays and store them in the compact harness format.
usage: fetch.py episode_ids.txt out.json
Each record: {id, info{TeamNames, seed, EpisodeId}, rewards, statuses, acts[t] = [seat0 action, seat1 action]}.
Already-present ids in out.json are skipped; the file is rewritten after every download."""
import sys, os, json, urllib.request, time
from concurrent.futures import ThreadPoolExecutor

URL = "https://www.kaggle.com/competitions/episodes/%d/replay.json"


def get(eid):
    for attempt in range(3):
        try:
            req = urllib.request.Request(URL % eid, headers={'Accept-Encoding': 'gzip'})
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
                if r.headers.get('Content-Encoding') == 'gzip':
                    import gzip
                    raw = gzip.decompress(raw)
                rep = json.loads(raw)
            steps = rep.get("steps") or []
            acts = []
            for s in steps:
                row = []
                for x in s:
                    a = x.get("action") if isinstance(x, dict) else None
                    row.append(a if isinstance(a, dict) else None)
                acts.append(row)
            info = rep.get("info") or {}
            return dict(id=eid, info=dict(TeamNames=info.get("TeamNames"), seed=info.get("seed"), EpisodeId=eid),
                        rewards=rep.get("rewards"), statuses=rep.get("statuses"), acts=acts)
        except Exception as e:
            err = e
            time.sleep(3)
    print('failed', eid, err, flush=True)
    return None


if __name__ == '__main__':
    ids = [int(x) for x in open(sys.argv[1]).read().split()]
    out = sys.argv[2]
    have = json.load(open(out, encoding='utf-8')) if os.path.exists(out) else []
    done = {d['id'] for d in have}
    todo = [i for i in ids if i not in done]
    print(len(todo), 'to fetch', flush=True)
    with ThreadPoolExecutor(4) as ex:
        for rec in ex.map(get, todo):
            if rec:
                have.append(rec)
                json.dump(have, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
                print('ok', rec['id'], rec['info']['TeamNames'], rec['rewards'], flush=True)
