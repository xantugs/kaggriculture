"""Elite route transplant test.

For every recorded elite game and every seat, replay that seat's recorded actions open-loop as OUR agent
(fresh private weed stream, like a real transplant) against a candidate in the other seat, in the recorded town
(shop sequence pinned to the recording). Each game is first replayed tape-vs-tape to check that the recording
reproduces on this engine (rec_ok) and to recover its shop sequence.

usage: eval_elite_routes.py games.jsonl[.gz] cand.py out.jsonl [teams=A,B|ALL] [maxgames] [seats=01]
Aggregates: per team, tape wins vs the candidate, mean margin, recorded reproduction count.
"""
import sys, os, json, gzip, random, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena')
sys.path.insert(0, '/home/user/kaggriculture/gold/harness')


def install_town(shops):
    """Decoupled weeds for both farms (private streams) and the recorded shop sequence, from day 0."""
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    orig = K._end_of_day
    def eod(state, env, day):
        obs0 = state[0].observation
        cfg = env.configuration
        bs = int(K.get(cfg, "boardSize", 10)); tpd = max(1, int(K.get(cfg, "turnsPerDay", 24)))
        chance = float(K.get(cfg, "weedSpawnChance", 0.005)); cap = int(K.get(cfg, "shedCapacity", 100))
        seed = env.info.get("seed", 0)
        for pid, farm in enumerate(obs0.farms):
            private = state[pid].observation.private
            K._daily_refresh_plants(farm, day, tpd)
            K._daily_refresh_animals(farm, day)
            rng = random.Random((seed * 1_000_003) ^ (day * 7919) ^ ((pid + 1) * 104_729))
            K._spawn_weeds(farm, bs, chance, rng)
            K._drop_inventories_to_shed(private, cap)
            farm["farmer"] = list(K._default_spawn(bs)); farm["hands"] = []; farm["hires_today"] = 0
            private["inventories"] = [{}]
        nd = day + 1
        town = obs0.town
        if nd > 0 and nd % 3 == 0 and len(town["unlocked_shops"]) < K.MAX_SHOP_INSTANCES:
            k = len(town["unlocked_shops"])
            town["unlocked_shops"].append(shops[k] if k < len(shops) else "BAKERY")
    K._end_of_day = eod
    return orig


def job(t):
    d, seats, cand = t
    import lean, pinned4
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    spawns, shops, rref = pinned4.reference(d)
    rec_ok = [int(x) for x in rref] == [int(x) for x in d['rewards']]
    out = []
    for s in seats:
        orig = install_town(shops)
        led = [collections.Counter(), collections.Counter()]
        FARMS = [None, None]
        oc = K._commit_unit
        def commit(op, item, price, farm, private, market, cap=100):
            ok = oc(op, item, price, farm, private, market, cap)
            if ok and FARMS[0] is not None:
                i = 0 if farm is FARMS[0] else 1
                if op == 'SELL': led[i][item] += price
                elif op == 'BUY_PRODUCT': led[i][item] -= price
                elif op == 'BUY_SEED': led[i]['seed'] -= price
                elif op == 'BUY_ANIMAL': led[i]['anim'] -= price
            return ok
        opm = K._process_market
        def pm(state, env):
            FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
            return opm(state, env)
        oh = K._do_hire
        def hire(farm, private, bs, mult=1):
            m0 = farm['money']; oh(farm, private, bs, mult)
            if FARMS[0] is not None:
                led[0 if farm is FARMS[0] else 1]['hire'] += farm['money'] - m0
        K._commit_unit = commit; K._process_market = pm; K._do_hire = hire
        t0 = time.time()
        try:
            A = lean.load(cand)
            ag = [None, None]
            ag[s] = pinned4._tape(d['acts'], s)
            ag[1 - s] = A
            r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
        finally:
            K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh
        tape, cd = r['r'][s], r['r'][1 - s]
        out.append(dict(gid=d['id'], seed=d['info']['seed'], team=d['info']['TeamNames'][s], seat=s,
                        opp_rec=d['info']['TeamNames'][1 - s], rec_tape=d['rewards'][s], rec_opp=d['rewards'][1 - s],
                        rec_ok=rec_ok, shops=shops, tape=tape, cand=cd,
                        m=(tape - cd) if tape is not None and cd is not None else None,
                        err=r['err'], tmax=r['tmax'], led_tape=dict(led[s]), led_cand=dict(led[1 - s]),
                        wall=round(time.time() - t0, 1)))
    return out


def load_games(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8') as fh:
        if path.endswith('.json'):
            return json.load(fh)
        return [json.loads(l) for l in fh if l.strip()]


if __name__ == '__main__':
    path, cand, out = sys.argv[1], sys.argv[2], sys.argv[3]
    teams = sys.argv[4] if len(sys.argv) > 4 else 'ALL'
    maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
    seats_arg = sys.argv[6] if len(sys.argv) > 6 else '01'
    want = None if teams == 'ALL' else set(teams.split(','))
    games = load_games(path)
    jobs = []
    for d in games:
        names = d['info']['TeamNames']
        seats = [s for s in (0, 1) if str(s) in seats_arg and (want is None or names[s] in want)]
        if seats and len(d['acts']) == 720:
            jobs.append((d, seats, cand))
    jobs = jobs[:maxg]
    res = []
    if os.environ.get('RESUME') and os.path.exists(out):
        # append to an interrupted run: keep its rows, skip games it already finished
        res = [json.loads(l) for l in open(out, encoding='utf-8') if l.strip()]
        done = {r['gid'] for r in res}
        jobs = [j for j in jobs if j[0]['id'] not in done]
        print(f'resuming: {len(res)} rows kept, {len(jobs)} games left', flush=True)
    print(f'{len(jobs)} games, cand {cand}', flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(out, 'a' if res else 'w', encoding='utf-8') as fh:
        for rows in ex.map(job, jobs):
            for r in rows:
                res.append(r); fh.write(json.dumps(r, ensure_ascii=False) + '\n')
            fh.flush()
    by = collections.defaultdict(list)
    for r in res:
        by[r['team']].append(r)
    print(f"{'team':28s} {'n':>4} {'tapeW':>5} {'win%':>5} {'margin':>8} {'tape$':>8} {'cand$':>8} {'rec$':>8} {'recOK':>6} {'errs':>4}")
    for team, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
        ok = [r for r in rs if r['m'] is not None]
        n = max(1, len(ok)); w = sum(r['m'] > 0 for r in ok)
        print(f"{team[:28]:28s} {len(rs):4d} {w:5d} {100*w/n:5.0f} {sum(r['m'] for r in ok)/n:+8.0f} {sum(r['tape'] for r in ok)/n:8.0f} {sum(r['cand'] for r in ok)/n:8.0f} {sum(r['rec_tape'] for r in ok)/n:8.0f} {sum(r['rec_ok'] for r in rs):6d} {sum(1 for r in rs if any(r['err'])):4d}")
    ok = [r for r in res if r['m'] is not None]
    n = max(1, len(ok)); w = sum(r['m'] > 0 for r in ok)
    print(f"ALL: tape wins {w}/{len(ok)} ({100*w/n:.0f}%), mean margin {sum(r['m'] for r in ok)/n:+.0f}, recOK {sum(r['rec_ok'] for r in res)}/{len(res)}, wall {time.time()-t0:.0f}s")
