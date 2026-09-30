"""lad_build.py : all live v33 games as an elite-gate panel (the rival's recorded seat, repaired, in its own town; the candidate
in our seat) -> gates/lad_v33_games.jsonl.gz + lad_v33_refs.jsonl (run with elite_gate.py run)."""
import sys, os, json, gzip
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
import elite_gate
G = 'gold/top10/gates/'
if __name__ == '__main__':
    games = [r for r in (json.loads(l) for l in open('gold/top10/research/opening/live_v33.jsonl', encoding='utf-8') if l.startswith('{')) if all(s == 'DONE' for s in r['statuses'])]
    with gzip.open(G + 'lad_v33_games.jsonl.gz', 'wt', encoding='utf-8') as fh:
        for g in games: fh.write(json.dumps(g, ensure_ascii=False) + '\n')
    jobs = [(g, 1 - g['meta']['seat']) for g in games]
    n = 0
    with ProcessPoolExecutor(6) as ex, open(G + 'lad_v33_refs.jsonl', 'w', encoding='utf-8') as fh:
        for r in ex.map(elite_gate._ref, jobs):
            if r: fh.write(json.dumps(r, ensure_ascii=False) + '\n'); n += 1
    print('built', n, 'of', len(games))
