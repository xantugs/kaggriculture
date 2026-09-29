"""fresh_gate_build.py OUTNAME DAY[,DAY...] MAXRANK CAP : an elite gate from fetched daily datasets (moon/elite/games_DAY.jsonl):
every seat of a team ranked <= MAXRANK on the current leaderboard (gold/top10/gates/lb_20260930.json), at most CAP seats per team,
full 720-step games only; writes gold/top10/gates/OUTNAME_games.jsonl.gz and OUTNAME_refs.jsonl (elite_gate's reference logs)."""
import sys, os, json, gzip, collections, time
sys.path.insert(0, os.path.join(os.getcwd(), 'arena')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/harness')); sys.path.insert(0, os.path.join(os.getcwd(), 'gold/elite'))
from concurrent.futures import ProcessPoolExecutor
import elite_gate

if __name__ == '__main__':
    name, days, maxrank, cap = sys.argv[1], sys.argv[2].split(','), int(sys.argv[3]), int(sys.argv[4])
    lb = {r['team']: r['rank'] for r in json.load(open('gold/top10/gates/lb_20260930.json', encoding='utf-8'))}
    cnt = collections.Counter(); jobs = []; keep = {}
    for d in days:
        for l in open('moon/elite/games_%s.jsonl' % d, encoding='utf-8'):
            try: g = json.loads(l)
            except Exception: continue
            if len(g.get('acts') or []) != 720 or not g.get('rewards') or None in g['rewards']: continue
            for s in (0, 1):
                t = g['info']['TeamNames'][s]
                if lb.get(t, 10 ** 6) <= maxrank and cnt[t] < cap:
                    cnt[t] += 1; jobs.append((g, s)); keep[g['id']] = g
    print(len(jobs), 'seats', dict(cnt.most_common()), flush=True)
    with gzip.open('gold/top10/gates/%s_games.jsonl.gz' % name, 'wt', encoding='utf-8') as fh:
        for g in keep.values(): fh.write(json.dumps(g, ensure_ascii=False) + '\n')
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '8'))) as ex, open('gold/top10/gates/%s_refs.jsonl' % name, 'w', encoding='utf-8') as fh:
        for r in ex.map(elite_gate._ref, jobs):
            fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush(); n += 1
            if n % 100 == 0: print(n, 'refs', int(time.time() - t0), 's', flush=True)
    print('done', n, 'refs', int(time.time() - t0), 's')
