"""Hybrid library test: donor elite route (repaired replay) + takeover controller from `start`, played in the TARGET
town (prefix-matched, different game) against a candidate; optionally also in the donor's own town.
usage: eval_hybrid_matched.py games.jsonl.gz cand.py prefix_matched.jsonl out.jsonl start [own=0|1] ['{gc overrides}']"""
import sys, os, json, time, collections, subprocess
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
BASES = '/home/user/kaggriculture/gold/elite/bases'

def ensure_hybrid(d, seat, start, over):
    from build_elite import build
    base = f'{BASES}/elite_{d["id"]}_{seat}.py'
    hyb = f'{BASES}/hyb_{d["id"]}_{seat}_s{start}.py'
    if not os.path.exists(base):
        build(d, seat, base)
    if not os.path.exists(hyb):
        o = dict(over); o['start'] = start
        subprocess.run([sys.executable, '/home/user/kaggriculture/gold/build.py', hyb, json.dumps(o), base], check=True, capture_output=True)
    return hyb

def job(t):
    import lean
    from eval_elite_routes import install_town
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    tgt, donor, ds, start, cand, over = t
    hyb = ensure_hybrid(donor, ds, start, over)
    orig = install_town(tgt['shops'])
    try:
        H = lean.load(hyb)
        ag = [None, None]; ag[ds] = H; ag[1 - ds] = lean.load(cand)
        r = lean.play(None, None, tgt['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    tel = dict(getattr(H, 'telemetry', {}) or {})
    tape, cd = r['r'][ds], r['r'][1 - ds]
    return dict(gid=tgt['gid'], team=tgt['team'], donor_gid=donor['id'], donor_team=donor['info']['TeamNames'][ds], start=start,
                tape=tape, cand=cd, m=(tape - cd) if tape is not None and cd is not None else None, err=r['err'],
                gc_errors=tel.get('gc_errors', 0), plain_m=tgt.get('plain_m'), own_m=tgt.get('own_m'))

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, cand, pm, out, start = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
    own = bool(int(sys.argv[6])) if len(sys.argv) > 6 else False
    over = json.loads(sys.argv[7]) if len(sys.argv) > 7 else {}
    rows = [json.loads(l) for l in open(pm)]
    games = {g['id']: g for g in load_games(path)}
    res_rows = [json.loads(l) for l in open('/home/user/kaggriculture/gold/elite/elite_vs_v100.jsonl')]
    seat_of = {(r['gid'], r['team']): r['seat'] for r in res_rows}
    shops_of = {r['gid']: r['shops'] for r in res_rows}
    seed_of = {r['gid']: r['seed'] for r in res_rows}
    jobs = []
    for r in rows:
        dg = games[r['donor_gid']]; ds = seat_of[(r['donor_gid'], r['donor_team'])]
        if own:
            tgt = dict(gid=r['donor_gid'], team=r['donor_team'], seed=seed_of[r['donor_gid']], shops=shops_of[r['donor_gid']], plain_m=None, own_m=None)
        else:
            tgt = dict(gid=r['gid'], team=r['team'], seed=seed_of[r['gid']], shops=shops_of[r['gid']], plain_m=r['m'], own_m=r['own_m'])
        jobs.append((tgt, dg, ds, start, cand, over))
    # build the bases/hybrids once, serially (cheap), so workers only play
    seen = set()
    for tgt, dg, ds, st, c, o in jobs:
        if (dg['id'], ds) not in seen:
            seen.add((dg['id'], ds)); ensure_hybrid(dg, ds, st, o)
    print(f'{len(jobs)} games, {len(seen)} donor hybrids, start {start}, own-town {own}', flush=True)
    t0 = time.time(); res = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(job, jobs):
            res.append(x); fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    ok = [x for x in res if x['m'] is not None]
    by = collections.defaultdict(list)
    for x in ok: by[x['donor_team'] if own else x['team']].append(x)
    print(f"{'team':18s} {'n':>4} {'W':>4} {'win%':>5} {'margin':>8} {'hyb$':>7} {'v100$':>7} {'gcErr':>5} | plain-route margin | own-town route margin")
    for team, xs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        w = sum(x['m'] > 0 for x in xs); n = len(xs)
        pl = [x['plain_m'] for x in xs if x['plain_m'] is not None]; ow = [x['own_m'] for x in xs if x['own_m'] is not None]
        print(f"{team[:18]:18s} {n:4d} {w:4d} {100*w/n:5.0f} {sum(x['m'] for x in xs)/n:+8.0f} {sum(x['tape'] for x in xs)/n:7.0f} {sum(x['cand'] for x in xs)/n:7.0f} {sum(x['gc_errors'] for x in xs):5d} | {(sum(pl)/len(pl)) if pl else float('nan'):+8.0f} | {(sum(ow)/len(ow)) if ow else float('nan'):+8.0f}")
    w = sum(x['m'] > 0 for x in ok); n = max(1, len(ok))
    print(f"ALL: hybrid wins {w}/{len(ok)} ({100*w/n:.0f}%), mean margin {sum(x['m'] for x in ok)/n:+.0f}, gc errors {sum(x['gc_errors'] for x in ok)}, errs {sum(1 for x in ok if any(x['err']))}, wall {time.time()-t0:.0f}s")
