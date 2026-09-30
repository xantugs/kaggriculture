"""vgate2.py PANEL OUT FILE... : run several agent files on one replay panel (rival = its recorded seat, repaired, in its own
town). Like vgate.py, but the games are loaded per chunk (env CHUNK, default 100 games) so a worker never holds a whole panel
(~3 MB per game), and env BAND=2400 restricts the panel to refs of that 100-rating band. NPROC (12), MAXTASKS (30) as before.
One row per (file, game) in OUT; resumable."""
import sys, os, json, gzip
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
G = 'gold/top10/gates/'
FILES = {'lad': (G + 'lad_v33_games.jsonl.gz', G + 'lad_v33_refs.jsonl'), 'f29': (G + 'fresh29_games.jsonl.gz', G + 'fresh29_refs.jsonl'),
         'f29s': (G + 'fresh29_games.jsonl.gz', G + 'fresh29s_refs.jsonl'), 'lad24': (G + 'lad24_games.jsonl.gz', G + 'lad24_refs.jsonl'),
         'crawl': (G + 'crawl_games.jsonl.gz', G + 'crawl_refs.jsonl')}
_W = {}


def _init(panel, gids):
    import elite_gate  # noqa
    gz, rf = FILES[panel]
    gids = set(gids)
    with gzip.open(gz, 'rt', encoding='utf-8') as fh:
        for l in fh:
            d = json.loads(l)
            if d['id'] in gids: _W[('game', d['id'])] = d
    for l in open(rf, encoding='utf-8'):
        r = json.loads(l)
        if r['gid'] in gids: _W[('ref', r['gid'], r['seat'])] = r


def _task(t):
    import elite_gate
    path, g, s = t
    try:
        x = elite_gate._play((_W[('game', g)], _W[('ref', g, s)], path))
        return dict(file=path, gid=g, seat=s, m=x['m'], us=x['us'], them=x['tape'], err=x['err'], tmax=max(x['tmax']) if x.get('tmax') else None,
                    tel={k: v for k, v in (x.get('tel') or {}).items() if k in ('gc_days', 'gc_div2_money', 'gc_route')} if x.get('tel') else None)
    except Exception as e:
        return dict(file=path, gid=g, seat=s, m=None, error=repr(e)[:200])


if __name__ == '__main__':
    panel, out, paths = sys.argv[1], sys.argv[2], sys.argv[3:]
    band = os.environ.get('BAND')
    refs = [json.loads(l) for l in open(FILES[panel][1], encoding='utf-8')]
    if band: refs = [r for r in refs if str(r.get('band')) == band]
    keys = [(r['gid'], r['seat']) for r in refs]
    done = set()
    if os.path.exists(out):
        for l in open(out, encoding='utf-8'):
            r = json.loads(l); done.add((r['file'], r['gid'], r['seat']))
    chunk = int(os.environ.get('CHUNK', 100)); nproc = int(os.environ.get('NPROC', 12)); maxt = int(os.environ.get('MAXTASKS', 120)) or None   # 0 = no worker recycling
    total = sum(1 for g, s in keys for p in paths if (p, g, s) not in done); n = 0
    print('%s%s: %d files x %d games -> %d tasks, chunks of %d games' % (panel, ' band ' + band if band else '', len(paths), len(keys), total, chunk), flush=True)
    with open(out, 'a', encoding='utf-8') as fo:
        for c0 in range(0, len(keys), chunk):
            ck = keys[c0:c0 + chunk]
            tasks = [(p, g, s) for g, s in ck for p in paths if (p, g, s) not in done]
            if not tasks: continue
            with ProcessPoolExecutor(nproc, initializer=_init, initargs=(panel, [g for g, s in ck]), max_tasks_per_child=maxt) as ex:
                for r in ex.map(_task, tasks, chunksize=2):
                    fo.write(json.dumps(r) + '\n'); fo.flush(); n += 1
                    if n % 200 == 0: print('  %d/%d' % (n, total), flush=True)
    print('done', n, flush=True)
