"""Repaired transplant at scale: every seat of the selected teams, repaired replay (outcome orders, plant trim,
drift-gated hire reservation) as our agent in the recorded town with fresh weeds, against a candidate.
usage: eval_repaired_own.py games.jsonl.gz cand.py out.jsonl [teams=A,B|ALL] [maxgames] [slack_min]"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

def job(t):
    from transplant import reference_log, transplant_play
    d, seats, cand, slack_min = t
    out = []
    for s in seats:
        ref = reference_log(d, s)
        t0 = time.time()
        r = transplant_play(d, s, cand, ref, slack_min=slack_min)
        tape, cd = r['r'][s], r['r'][1 - s]
        out.append(dict(gid=d['id'], seed=d['info']['seed'], team=d['info']['TeamNames'][s], seat=s, opp_rec=d['info']['TeamNames'][1 - s],
                        rec_tape=d['rewards'][s], rec_opp=d['rewards'][1 - s], rec_ok=ref['ok'], shops=ref['shops'], tape=tape, cand=cd,
                        m=(tape - cd) if tape is not None and cd is not None else None, err=r['err'], tmax=r['tmax'], wall=round(time.time() - t0, 1)))
    return out

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, cand, out = sys.argv[1], sys.argv[2], sys.argv[3]
    teams = sys.argv[4] if len(sys.argv) > 4 else 'ALL'
    maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
    slack_min = int(sys.argv[6]) if len(sys.argv) > 6 else 20
    want = None if teams == 'ALL' else set(teams.split(','))
    jobs = []
    for d in load_games(path):
        names = d['info']['TeamNames']
        seats = [s for s in (0, 1) if want is None or names[s] in want]
        if seats and len(d['acts']) == 720:
            jobs.append((d, seats, cand, slack_min))
    jobs = jobs[:maxg]
    print(f'{len(jobs)} games, cand {cand}, slack_min {slack_min}', flush=True)
    t0 = time.time(); res = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for rows in ex.map(job, jobs):
            for r in rows:
                res.append(r); fh.write(json.dumps(r, ensure_ascii=False) + '\n')
            fh.flush()
    by = collections.defaultdict(list)
    for r in res: by[r['team']].append(r)
    print(f"{'team':26s} {'n':>4} {'robust%':>7} {'ratio':>6} {'W':>4} {'win%':>5} {'margin':>8} {'tape$':>7} {'v100$':>7} {'rec$':>7} {'recOK':>5} {'errs':>4}")
    for team, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        ok = [r for r in rs if r['m'] is not None]; n = max(1, len(ok))
        ratios = [r['tape'] / r['rec_tape'] for r in ok if r['rec_tape'] > 0]
        rob = sum(1 for x in ratios if x >= 0.9)
        w = sum(r['m'] > 0 for r in ok)
        print(f"{team[:26]:26s} {len(rs):4d} {100*rob/max(1,len(ratios)):7.0f} {sum(ratios)/max(1,len(ratios)):6.2f} {w:4d} {100*w/n:5.0f} {sum(r['m'] for r in ok)/n:+8.0f} {sum(r['tape'] for r in ok)/n:7.0f} {sum(r['cand'] for r in ok)/n:7.0f} {sum(r['rec_tape'] for r in ok)/n:7.0f} {sum(r['rec_ok'] for r in rs):5d} {sum(1 for r in rs if any(r['err'])):4d}")
    ok = [r for r in res if r['m'] is not None]; n = max(1, len(ok)); w = sum(r['m'] > 0 for r in ok)
    print(f"ALL: repaired tape wins {w}/{len(ok)} ({100*w/n:.0f}%), mean margin {sum(r['m'] for r in ok)/n:+.0f}, mean ratio {sum(r['tape']/r['rec_tape'] for r in ok if r['rec_tape']>0)/n:.2f}, wall {time.time()-t0:.0f}s")
