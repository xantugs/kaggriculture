"""Build the current-top gate from Kaggle's daily top-tier datasets (the elite gate, rebuilt on this week's teams).
usage: build_gate26.py out_prefix per_team team1,team2,... games1.jsonl[,games2.jsonl.gz ...]
Writes <out_prefix>_games.jsonl.gz (the selected games, compact form) and <out_prefix>_refs.jsonl (reference logs,
one row per seat, the format elite_gate.py run reads). Seats are spread evenly over each team's games by episode id;
games whose recording does not reproduce (ref ok False) are dropped from the refs."""
import sys, os, json, gzip, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.path.insert(0, '/home/user/kaggriculture/gold/elite')


def load(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def ref_job(t):
    import elite_gate
    return elite_gate._ref(t)


if __name__ == '__main__':
    prefix, per_team, teams = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(',')
    files = sys.argv[4].split(',')
    games = {}
    for f in files:
        for d in load(f):
            if len(d.get('acts') or []) == 720 and d.get('rewards') and None not in d['rewards']:
                games[d['id']] = d
    by_team = collections.defaultdict(list)
    for gid in sorted(games):
        names = games[gid]['info']['TeamNames']
        for s in (0, 1):
            if names[s] in teams:
                by_team[names[s]].append((gid, s))
    pick = []
    for t in teams:
        seats = by_team.get(t, [])
        if not seats:
            print('no seats for', t); continue
        k = min(per_team, len(seats))
        idx = sorted({int(i * len(seats) / k) for i in range(k)})
        pick += [seats[i] for i in idx]
        print(f'{t}: {len(seats)} seats, picked {len(idx)}', flush=True)
    used = sorted({gid for gid, _ in pick})
    with gzip.open(prefix + '_games.jsonl.gz', 'wt', encoding='utf-8') as fh:
        for gid in used:
            fh.write(json.dumps(games[gid], ensure_ascii=False) + '\n')
    jobs = [(games[gid], s) for gid, s in pick]
    n_ok = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(prefix + '_refs.jsonl', 'w', encoding='utf-8') as fh:
        for r in ex.map(ref_job, jobs):
            if r['ok']:
                n_ok += 1
                fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
            else:
                print('not reproduced', r['gid'], r['seat'], r['team'], flush=True)
    print('seats', len(jobs), 'reproduced', n_ok, 'games', len(used))
