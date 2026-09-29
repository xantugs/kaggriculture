"""ladder_gate.py build | run CAND OUT : the v33 ladder games against C2S3 / new-meta rivals as an elite-gate panel (the rival's
recorded seat, repaired, in its own town; the candidate in our seat)."""
import sys, os, json, gzip
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
import elite_gate
D = 'gold/top10/research/v33loss/'
GIDS = [115333932, 115335380, 115338309, 115336805, 115339671, 115332494, 115334960, 115345249,115343876]
if __name__ == '__main__':
    games = {r['id']: r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{')) if r['id'] in GIDS}
    if sys.argv[1] == 'build':
        jobs = [(games[g], 1 - games[g]['meta']['seat']) for g in GIDS]
        with gzip.open(D + 'ladder_games.jsonl.gz', 'wt', encoding='utf-8') as fh:
            for g in GIDS: fh.write(json.dumps(games[g], ensure_ascii=False) + '\n')
        with ProcessPoolExecutor(4) as ex, open(D + 'ladder_refs.jsonl', 'w', encoding='utf-8') as fh:
            for r in ex.map(elite_gate._ref, jobs): fh.write(json.dumps(r, ensure_ascii=False) + '\n')
        print('built', len(jobs))
    else:
        cand, out = sys.argv[2], sys.argv[3]
        R = [json.loads(l) for l in open(D + 'ladder_refs.jsonl', encoding='utf-8')]
        with ProcessPoolExecutor(4) as ex, open(out, 'w', encoding='utf-8') as fh:
            for x in ex.map(elite_gate._play, [(games[r['gid']], r, cand) for r in R]):
                fh.write(json.dumps(x, ensure_ascii=False) + '\n')
