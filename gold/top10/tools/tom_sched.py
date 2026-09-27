"""Elite-gate run with a per-day tomato trace of both farms (rows compatible with paircmp.py).
usage: tom_sched.py games.jsonl.gz refs.jsonl cand.py out.jsonl [maxseats]
Per day and side: tomato plants alive / planted today / ripe units, tomato units and $ sold, the tomato quote and
book at the end of the day, money, hands, empty unlocked tiles, quadrants. Plus the controller's _GC_REPORT."""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

def _play(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    pinned_eod = K._end_of_day
    led = [collections.Counter(), collections.Counter()]; FARMS = [None, None]; DAY = [0]
    sold = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    days = [[], []]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL':
                led[i][item] += price
                if item == 'TOMATO': sold[i][DAY[0]]['u'] += 1; sold[i][DAY[0]]['$'] += price
            elif op == 'BUY_PRODUCT': led[i][item] -= price
            elif op == 'BUY_SEED':
                led[i]['seed'] -= price
                if item == 'TOMATO': sold[i][DAY[0]]['seed'] += 1
            elif op == 'BUY_ANIMAL': led[i]['anim'] -= price
        return ok
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        DAY[0] = int(K.get(state[0].observation, 'step', 0)) // 24
        return opm(state, env)
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None: led[0 if farm is FARMS[0] else 1]['hire'] += farm['money'] - m0
    def eod(state, env, day):
        obs0 = state[0].observation
        mk = obs0.market
        for pid, farm in enumerate(obs0.farms):
            alive = planted = ripe = free = 0; pdays = collections.Counter(); cen = collections.Counter()
            quads = list(farm['unlocked_quadrants'])
            for y, row in enumerate(farm['tiles']):
                for x, tile in enumerate(row):
                    if isinstance(tile, dict) and tile.get('crop') == 'TOMATO':
                        alive += 1; ripe += tile.get('yield_units', 0); pdays[tile.get('planted_day')] += 1
                        if tile.get('planted_day') == day: planted += 1
                    elif tile is None: free += 1
                    if isinstance(tile, dict):
                        k = tile.get('crop') or tile.get('animal')
                        if k: cen[k[:2]] += 1
                        if tile.get('crop') and tile.get('planted_day') == day: cen['+' + tile['crop'][:2]] += 1
            sd = sold[pid][day]
            days[pid].append([day, alive, planted, ripe, sd['u'], sd['$'], sd['seed'], round(farm['money']), len(farm['hands']), free, len(quads), dict(cen)])
        days[0][-1].append([mk['prices']['TOMATO'], mk['inventory']['TOMATO']])
        days[0][-1].append({k: mk['prices'][k] for k in ('WHEAT', 'CARROT', 'STRAWBERRY', 'EGG', 'MILK', 'WOOL', 'FERTILIZER', 'MELON')})
        return pinned_eod(state, env, day)
    K._commit_unit = commit; K._process_market = pm; K._do_hire = hire; K._end_of_day = eod
    t0 = time.time(); A = None
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh
    tape, cd = r['r'][s], r['r'][1 - s]
    g = getattr(A, '__globals__', {}) or {}
    rep = g.get('_GC_REPORT') or {}
    rep = {k: v for k, v in rep.items() if isinstance(v, (int, float, str))}
    for k in ('_V219_REPORT',):
        v = g.get(k)
        if isinstance(v, dict): rep['v219'] = {kk: vv for kk, vv in v.items() if isinstance(vv, (int, float)) and vv}
    for k in ('_V219_N', '_V219_DAY'):
        v = g.get(k)
        if isinstance(v, list): rep[k] = v[0]
    return dict(gid=ref['gid'], seat=s, team=ref['team'], cand=cand, tape=tape, us=cd, m=(cd - tape) if tape is not None and cd is not None else None,
                err=r['err'], tmax=r['tmax'], rec_tape=ref['rec_tape'], wall=round(time.time() - t0, 1),
                led_us=dict(led[1 - s]), led_elite=dict(led[s]), gc=rep, tdays_us=days[1 - s], tdays_el=days[s], shops=ref['shops'])

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, cand, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
    R = [json.loads(l) for l in open(refs, encoding='utf-8')][:maxg]
    want = {r['gid'] for r in R}
    games = {g['id']: g for g in load_games(path) if g['id'] in want}
    jobs = [(games[r['gid']], r, cand) for r in R]
    t0 = time.time(); res = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(_play, jobs):
            res.append(x); fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    ok = [x for x in res if x['m'] is not None]
    w = sum(x['m'] > 0 for x in ok); n = max(1, len(ok))
    print(f"{cand}: {w}-{len(ok)-w} of {len(ok)}  margin {sum(x['m'] for x in ok)/n:+.0f}  errs {sum(1 for x in ok if any(x['err']))}  tmax {max(max(x['tmax']) for x in ok):.3f}  wall {time.time()-t0:.0f}s")
