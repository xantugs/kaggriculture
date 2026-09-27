"""Run the hire-logging research build on chosen gate seats; attach the per-day hire-search log to each row.
usage: hirelog_run.py games.jsonl.gz refs.jsonl cand.py out.jsonl gid:seat,gid:seat,...   (or a file of 'gid seat' lines)"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concurrent.futures import ProcessPoolExecutor
import labour_probe as LP

def job(t):
    d, ref, cand = t
    fd, p = tempfile.mkstemp(suffix='.jsonl'); os.close(fd)
    os.environ['LAB_HIRELOG'] = p
    try:
        row = LP._gate_job((d, ref, cand))
        row['hirelog'] = [json.loads(l) for l in open(p)]
    finally:
        os.remove(p)
    return row

if __name__ == '__main__':
    sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
    from eval_elite_routes import load_games
    gpath, refs, cand, out, sel = sys.argv[1:6]
    if os.path.exists(sel):
        want = {tuple(map(int, l.split())) for l in open(sel) if l.strip()}
    else:
        want = {tuple(map(int, s.split(':'))) for s in sel.split(',')}
    order = {k: i for i, k in enumerate([tuple(map(int, l.split())) for l in open(sel) if l.strip()] if os.path.exists(sel) else [tuple(map(int, s.split(":"))) for s in sel.split(",")])}
    R = sorted([r for r in map(json.loads, open(refs, encoding="utf-8")) if (r["gid"], r["seat"]) in want], key=lambda r: order[(r["gid"], r["seat"])])
    gids = {r['gid'] for r in R}
    games = {g['id']: g for g in load_games(gpath) if g['id'] in gids}
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(job, [(games[r['gid']], r, cand) for r in R]):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    print('done', len(R))
