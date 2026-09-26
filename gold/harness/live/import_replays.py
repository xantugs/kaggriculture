"""Import Kaggle Kaggriculture replays (raw episode JSON with 'steps', or the compact {id, info, rewards, acts} form,
as .json / .json.gz / .jsonl / .zip, files or directories) into one compact list usable by pinned4.py.
usage: import_replays.py out.json path [path ...] [--team offhand]"""
import sys, os, json, gzip, zipfile, io


def _compact(rep, name='?'):
    if not isinstance(rep, dict):
        return None
    if 'acts' in rep and 'info' in rep:
        return rep
    steps = rep.get('steps')
    if not steps:
        return None
    acts = [[(x.get('action') if isinstance(x, dict) and isinstance(x.get('action'), dict) else None) for x in s] for s in steps]
    info = rep.get('info') or {}
    cfg = rep.get('configuration') or {}
    seed = info.get('seed', cfg.get('seed'))
    eid = info.get('EpisodeId') or rep.get('id') or name
    names = info.get('TeamNames') or [a.get('Name') if isinstance(a, dict) else None for a in (info.get('Agents') or [])]
    rewards = rep.get('rewards')
    if rewards is None and steps:
        rewards = [x.get('reward') if isinstance(x, dict) else None for x in steps[-1]]
    statuses = rep.get('statuses') or ([x.get('status') for x in steps[-1]] if steps else None)
    return dict(id=eid, info=dict(TeamNames=names, seed=seed, EpisodeId=eid), rewards=rewards, statuses=statuses, acts=acts)


def _load_blob(raw, name):
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    txt = raw.decode('utf-8')
    out = []
    try:
        obj = json.loads(txt)
        objs = obj if isinstance(obj, list) else [obj]
    except json.JSONDecodeError:
        objs = [json.loads(l) for l in txt.splitlines() if l.strip()]
    for o in objs:
        c = _compact(o, name)
        if c:
            out.append(c)
    return out


def load_any(path):
    out = []
    if os.path.isdir(path):
        for f in sorted(os.listdir(path)):
            out += load_any(os.path.join(path, f))
        return out
    if path.endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.endswith(('.json', '.json.gz', '.jsonl')):
                    out += _load_blob(z.read(n), n)
        return out
    if path.endswith(('.json', '.gz', '.jsonl')):
        out += _load_blob(open(path, 'rb').read(), os.path.basename(path))
    return out


if __name__ == '__main__':
    args = sys.argv[1:]
    team = 'offhand'
    if '--team' in args:
        i = args.index('--team'); team = args[i + 1]; del args[i:i + 2]
    out, paths = args[0], args[1:]
    games, seen = [], set()
    for p in paths:
        for g in load_any(p):
            if g['id'] in seen:
                continue
            seen.add(g['id']); games.append(g)
    json.dump(games, open(out, 'w'))
    for g in games:
        n = g['info']['TeamNames']; r = g['rewards']
        P = n.index(team) if n and team in n else None
        tag = '?' if P is None else ('WIN' if r[P] > r[1 - P] else 'LOSS')
        print(g['id'], 'seed', g['info']['seed'], n, r, 'steps', len(g['acts']), 'us', P, tag)
    print(len(games), 'games ->', out)
