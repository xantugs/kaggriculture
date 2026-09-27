"""Library test: for each target game, replay a DONOR route from a different game whose first two shops match,
in the target's town (shops pinned), against a candidate. Donor = highest recorded margin among matching games of the
robust scripted teams. usage: eval_prefix_matched.py games.jsonl.gz cand.py results.jsonl out.jsonl [teams] [max]"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

def job(t):
    import lean, pinned4
    from eval_elite_routes import install_town
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    tgt, donor_acts, ds, cand = t
    orig = install_town(tgt['shops'])
    try:
        ag = [None, None]; ag[ds] = pinned4._tape(donor_acts, ds); ag[1 - ds] = lean.load(cand)
        r = lean.play(None, None, tgt['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    tape, cd = r['r'][ds], r['r'][1 - ds]
    return dict(gid=tgt['gid'], team=tgt['team'], donor_gid=tgt['donor_gid'], donor_team=tgt['donor_team'], prefix=tgt['shops'][:2],
                tape=tape, cand=cd, m=(tape - cd) if tape is not None and cd is not None else None, err=r['err'],
                own_m=tgt['own_m'], rec_tape=tgt['rec_tape'])

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, cand, res, out = sys.argv[1:5]
    teams = set((sys.argv[5] if len(sys.argv) > 5 else 'Sida Zuo,Yannik Schiffner,Otter Vibe,binghua').split(','))
    maxn = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
    rows = [json.loads(l) for l in open(res)]
    lib = [r for r in rows if r['team'] in teams and r['m'] is not None and r['tape'] >= 0.9 * r['rec_tape']]
    byp = collections.defaultdict(list)
    for r in lib: byp[tuple(r['shops'][:2])].append(r)
    games = {g['id']: g for g in load_games(path)}
    jobs = []
    for r in lib:
        pool = [x for x in byp[tuple(r['shops'][:2])] if x['gid'] != r['gid']]
        if not pool: continue
        donor = max(pool, key=lambda x: x['rec_tape'] - x['rec_opp'])
        tgt = dict(gid=r['gid'], team=r['team'], seed=r['seed'], shops=r['shops'], donor_gid=donor['gid'], donor_team=donor['team'], own_m=r['m'], rec_tape=r['rec_tape'])
        jobs.append((tgt, games[donor['gid']]['acts'], donor['seat'], cand))
    jobs = jobs[:maxn]
    print(f'{len(jobs)} matched targets from {len(lib)} library routes, {len(byp)} prefixes', flush=True)
    t0 = time.time(); res_rows = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(job, jobs):
            res_rows.append(x); fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    ok = [x for x in res_rows if x['m'] is not None]
    by = collections.defaultdict(list)
    for x in ok: by[x['team']].append(x)
    print(f"{'target team':18s} {'n':>4} {'donorW':>6} {'win%':>5} {'margin':>8} | own-town win% {'':>4} own margin")
    for team, xs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        w = sum(x['m'] > 0 for x in xs); n = len(xs)
        print(f"{team[:18]:18s} {n:4d} {w:6d} {100*w/n:5.0f} {sum(x['m'] for x in xs)/n:+8.0f} | {100*sum(x['own_m']>0 for x in xs)/n:5.0f} {'':>8} {sum(x['own_m'] for x in xs)/n:+8.0f}")
    w = sum(x['m'] > 0 for x in ok); n = max(1, len(ok))
    print(f"ALL: donor wins {w}/{len(ok)} ({100*w/n:.0f}%), mean margin {sum(x['m'] for x in ok)/n:+.0f}; same targets own-town: {100*sum(x['own_m']>0 for x in ok)/n:.0f}% {sum(x['own_m'] for x in ok)/n:+.0f}; wall {time.time()-t0:.0f}s")
