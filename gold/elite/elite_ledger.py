"""Ledger replay of the elite dump (jsonl.gz): per-seat sales/buys/hires/land and farm composition every 3 days,
using gold/harness/ledger_replay.one. usage: elite_ledger.py games.jsonl.gz out.jsonl [nproc]"""
import sys, os, json
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

def one(d):
    from ledger_replay import one as _one
    r = _one(d)
    r['seed'] = d['info']['seed']
    return r

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, out = sys.argv[1], sys.argv[2]
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    games = [g for g in load_games(path) if len(g['acts']) == 720]
    print(f'{len(games)} games', flush=True)
    n_ok = 0
    with ProcessPoolExecutor(nproc) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(one, games):
            n_ok += r['ok']; fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
    print(f'done {len(games)}, reproduced {n_ok}', flush=True)
