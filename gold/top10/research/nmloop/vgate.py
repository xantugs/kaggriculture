"""vgate.py PANEL OUT VERSION_FILE... : run several agent files on one replay panel (rival = its recorded seat, repaired, in its
own town) in a single 16-process pool over (file, game) pairs. PANEL = lad (the 115+ live v33 games) or f29 (the 656 fresh29
top-team seats). One row per (file, game) in OUT; resumable."""
import sys, os, json, gzip, collections
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
G = 'gold/top10/gates/'
FILES = {'lad': (G + 'lad_v33_games.jsonl.gz', G + 'lad_v33_refs.jsonl'), 'f29': (G + 'fresh29_games.jsonl.gz', G + 'fresh29_refs.jsonl'), 'f29s': (G + 'fresh29_games.jsonl.gz', G + 'fresh29s_refs.jsonl'), 'lad24': (G + 'lad24_games.jsonl.gz', G + 'lad24_refs.jsonl'), 'crawl': (G + 'crawl_games.jsonl.gz', G + 'crawl_refs.jsonl')}
_W = {}


def _init(panel):
    import elite_gate  # noqa
    gz, rf = FILES[panel]
    with gzip.open(gz, 'rt', encoding='utf-8') as fh:
        for l in fh:
            d = json.loads(l); _W[('game', d['id'])] = d
    for l in open(rf, encoding='utf-8'):
        r = json.loads(l); _W[('ref', r['gid'], r['seat'])] = r


def _task(t):
    import elite_gate
    path, g, s = t
    try:
        x = elite_gate._play((_W[('game', g)], _W[('ref', g, s)], path))
        return dict(file=path, gid=g, seat=s, m=x['m'], us=x['us'], them=x['tape'], err=x['err'], tmax=max(x['tmax']) if x.get('tmax') else None)
    except Exception as e:
        return dict(file=path, gid=g, seat=s, m=None, error=repr(e)[:200])


if __name__ == '__main__':
    panel, out, paths = sys.argv[1], sys.argv[2], sys.argv[3:]
    keys = [(r['gid'], r['seat']) for r in (json.loads(l) for l in open(FILES[panel][1], encoding='utf-8'))]
    done = set()
    if os.path.exists(out):
        for l in open(out, encoding='utf-8'):
            r = json.loads(l); done.add((r['file'], r['gid'], r['seat']))
    tasks = [(p, g, s) for g, s in keys for p in paths if (p, g, s) not in done]   # interleave files so partial results cover all
    print('%s: %d files x %d games -> %d tasks' % (panel, len(paths), len(keys), len(tasks)), flush=True)
    with ProcessPoolExecutor(int(os.environ.get('NPROC', 12)), initializer=_init, initargs=(panel,), max_tasks_per_child=int(os.environ.get('MAXTASKS', 30))) as ex, open(out, 'a', encoding='utf-8') as fo:
        for n, r in enumerate(ex.map(_task, tasks, chunksize=2)):
            fo.write(json.dumps(r) + '\n'); fo.flush()
            if n % 200 == 0: print('  %d/%d' % (n, len(tasks)), flush=True)
