"""Elite gate: a candidate vs repaired elite recordings in their own towns, with reference logs cached on disk.
usage: elite_gate.py build  games.jsonl.gz refs.json [teams] [max_per_team]      # cache hands/money/outcomes/shops
       elite_gate.py run    games.jsonl.gz refs.json cand.py out.jsonl [maxgames]  # play the candidate
"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def _ref(t):
    from transplant import reference_log
    d, s = t
    r = reference_log(d, s)
    return dict(gid=d['id'], seat=s, team=d['info']['TeamNames'][s], opp=d['info']['TeamNames'][1 - s], seed=d['info']['seed'],
                rec_tape=d['rewards'][s], rec_opp=d['rewards'][1 - s], hands=r['hands'], money=r['money'],
                outcomes={str(k): v for k, v in r['outcomes'].items()}, shops=r['shops'], ok=r['ok'])

def _play(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    led = [collections.Counter(), collections.Counter()]; FARMS = [None, None]
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
        if FARMS[0] is not None: led[0 if farm is FARMS[0] else 1]['hire'] += farm['money'] - m0
    K._commit_unit = commit; K._process_market = pm; K._do_hire = hire
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh
    tape, cd = r['r'][s], r['r'][1 - s]
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    return dict(gid=ref['gid'], seat=s, team=ref['team'], cand=cand, tape=tape, us=cd, m=(cd - tape) if tape is not None and cd is not None else None,
                err=r['err'], tmax=r['tmax'], rec_tape=ref['rec_tape'], wall=round(time.time() - t0, 1),
                led_us=dict(led[1 - s]), led_elite=dict(led[s]), tel=tel)

if __name__ == '__main__':
    from eval_elite_routes import load_games
    mode = sys.argv[1]
    if mode == 'build':
        path, refs = sys.argv[2], sys.argv[3]
        teams = sys.argv[4].split(',') if len(sys.argv) > 4 else ['DSM', 'Unknown Mother-Goose', 'M & M & P & Q', 'Majkel1337', 'QQ', 'Sida Zuo', 'Yannik Schiffner']
        maxp = int(sys.argv[5]) if len(sys.argv) > 5 else 40
        cnt = collections.Counter(); jobs = []
        for d in load_games(path):
            for s in (0, 1):
                t = d['info']['TeamNames'][s]
                if t in teams and cnt[t] < maxp and len(d['acts']) == 720:
                    cnt[t] += 1; jobs.append((d, s))
        print(f'{len(jobs)} seats: {dict(cnt)}', flush=True)
        with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(refs, 'w', encoding='utf-8') as fh:
            for r in ex.map(_ref, jobs):
                fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
        print('cached', len(jobs))
    else:
        path, refs, cand, out = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
        maxg = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
        R = [json.loads(l) for l in open(refs, encoding='utf-8')][:maxg]
        games = {g['id']: g for g in load_games(path)}
        jobs = [(games[r['gid']], r, cand) for r in R]
        t0 = time.time(); res = []
        with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
            for x in ex.map(_play, jobs):
                res.append(x); fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
        ok = [x for x in res if x['m'] is not None]
        by = collections.defaultdict(list)
        for x in ok: by[x['team']].append(x)
        print(f"{'team':22s} {'n':>4} {'W':>4} {'win%':>5} {'margin':>8} {'us$':>7} {'elite$':>7}")
        for team, xs in sorted(by.items(), key=lambda kv: -len(kv[1])):
            w = sum(x['m'] > 0 for x in xs); n = len(xs)
            print(f"{team[:22]:22s} {n:4d} {w:4d} {100*w/n:5.0f} {sum(x['m'] for x in xs)/n:+8.0f} {sum(x['us'] for x in xs)/n:7.0f} {sum(x['tape'] for x in xs)/n:7.0f}")
        w = sum(x['m'] > 0 for x in ok); n = max(1, len(ok))
        print(f"{cand}: {w}-{len(ok)-w} of {len(ok)} ({100*w/n:.0f}%)  margin {sum(x['m'] for x in ok)/n:+.0f}  errs {sum(1 for x in ok if any(x['err']))}  tmax {max(max(x['tmax']) for x in ok):.3f}  wall {time.time()-t0:.0f}s")
