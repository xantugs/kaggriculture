"""Per-day ledger of a candidate and a repaired elite in the elite's town (elite_gate._play set-up), for the endgame study.
usage: day_led.py games.jsonl.gz refs.jsonl cand.py out.jsonl [maxseats] [skip_gids_file]
Per seat and farm, per day: money at end of day, hires (count, $), market $ and units per product (sold / bought),
plantings by crop, tiles by crop, ripe units on tiles, goods held at end of day (shed + carried, before the night drop),
the shed after the drop; for days >= 22 also per-step sales by product.
"""
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
    orig_eod = install_town(ref['shops'])
    pinned_eod = K._end_of_day
    days = [[], []]
    mk = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    steps = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    FARMS = [None, None]; STEP = [0]
    FINAL = [None, None]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            dd = STEP[0] // 24
            if op == 'SELL':
                mk[i][dd]['u_' + item] += 1; mk[i][dd]['$_' + item] += price
                if dd >= 22: steps[i][STEP[0]]['u_' + item] += 1; steps[i][STEP[0]]['$_' + item] += price
            elif op == 'BUY_PRODUCT': mk[i][dd]['bu_' + item] += 1; mk[i][dd]['b$_' + item] += price
            elif op == 'BUY_SEED': mk[i][dd]['seed_' + item] += 1; mk[i][dd]['seed$'] += price
            elif op == 'BUY_ANIMAL': mk[i][dd]['anim_' + item] += 1; mk[i][dd]['anim$'] += price
        return ok
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = int(K.get(state[0].observation, 'step', 0))
        out = opm(state, env)
        if STEP[0] >= 718:
            obs0 = state[0].observation
            for pid, farm in enumerate(obs0.farms):
                private = state[pid].observation.private
                held = collections.Counter({k: v for k, v in private['shed'].items() if v})
                for inv in private.get('inventories', []) or []:
                    for k, v in (inv or {}).items():
                        if v: held[k] += v
                ripe = collections.Counter()
                for row in farm['tiles']:
                    for tile in row:
                        if isinstance(tile, dict) and (tile.get('crop') or tile.get('animal')) and tile.get('yield_units'):
                            ripe[tile.get('crop') or tile.get('animal')] += tile['yield_units']
                FINAL[pid] = dict(held=dict(held), ripe=dict(ripe), prices={k: int(v) for k, v in obs0.market['prices'].items()})
        return out
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None and farm['money'] != m0:
            i = 0 if farm is FARMS[0] else 1
            mk[i][STEP[0] // 24]['hire$'] += m0 - farm['money']; mk[i][STEP[0] // 24]['hires'] += 1
    def eod(state, env, day):
        obs0 = state[0].observation
        pre = []
        for pid, farm in enumerate(obs0.farms):
            private = state[pid].observation.private
            c = collections.Counter(); planted = collections.Counter(); ripe = collections.Counter(); ages = collections.Counter()
            for y, row in enumerate(farm['tiles']):
                for x, tile in enumerate(row):
                    if isinstance(tile, dict):
                        if tile.get('crop'):
                            c[tile['crop']] += 1
                            if tile.get('planted_day') == day: planted[tile['crop']] += 1
                            ripe[tile['crop']] += tile.get('yield_units', 0) or 0
                        elif tile.get('animal'):
                            c[tile['animal']] += 1; ripe[tile['animal']] += tile.get('yield_units', 0) or 0
                        elif tile.get('kind') == 'WEED': c['WEED'] += 1
            held = collections.Counter({k: v for k, v in private['shed'].items() if v})
            for inv in private.get('inventories', []) or []:
                for k, v in (inv or {}).items():
                    if v: held[k] += v
            pre.append(dict(day=day, money=round(farm['money']), land=len(farm['unlocked_quadrants']), tiles=dict(c), planted=dict(planted),
                            ripe=dict(ripe), held=dict(held), mkt=dict(mk[pid][day])))
        out = pinned_eod(state, env, day)
        for pid, farm in enumerate(obs0.farms):
            private = state[pid].observation.private
            pre[pid]['shed_post'] = {k: v for k, v in private['shed'].items() if v}
            rp = collections.Counter()
            for row in farm['tiles']:
                for tile in row:
                    if isinstance(tile, dict) and (tile.get('crop') or tile.get('animal')) and tile.get('yield_units'):
                        rp[tile.get('crop') or tile.get('animal')] += tile['yield_units']
            pre[pid]['ripe_post'] = dict(rp)
            pre[pid]['px'] = {k: int(v) for k, v in obs0.market['prices'].items()} if pid == 0 else None
            days[pid].append(pre[pid])
        return out
    VB = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    oau = K._apply_unit_action
    MV = set(K.FARMER_MOVES)
    def au(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        if FARMS[0] is not None and isinstance(action, list) and action:
            i = 0 if farm is FARMS[0] else 1
            op = action[0]
            VB[i][day]['MOVE' if op in MV else str(op)] += 1
        return oau(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
    K._commit_unit = commit; K._process_market = pm; K._end_of_day = eod; K._do_hire = hire; K._apply_unit_action = au
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig_eod; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh; K._apply_unit_action = oau
    # prices: town quotes at end are not needed; keep per-step sales for days >= 22
    st = [{str(k): dict(v) for k, v in steps[i].items()} for i in (0, 1)]
    return dict(gid=ref['gid'], seat=s, team=ref['team'], shops=ref['shops'], elite=r['r'][s], us=r['r'][1 - s], err=r['err'],
                m=(r['r'][1 - s] - r['r'][s]) if r['r'][s] is not None and r['r'][1 - s] is not None else None,
                days_elite=days[s], days_us=days[1 - s], final_elite=FINAL[s], final_us=FINAL[1 - s], mkt29_elite=dict(mk[s][29]), mkt29_us=dict(mk[1 - s][29]), verbs_elite={str(k): dict(v) for k, v in VB[s].items()}, verbs_us={str(k): dict(v) for k, v in VB[1 - s].items()}, steps_elite=st[s], steps_us=st[1 - s], wall=round(time.time() - t0, 1))

if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, cand, out = sys.argv[1:5]
    maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
    R = [json.loads(l) for l in open(refs, encoding='utf-8')][:maxg]
    done = set()
    if os.path.exists(out):
        for l in open(out, encoding='utf-8'):
            try: x = json.loads(l); done.add((x['gid'], x['seat']))
            except Exception: pass
    R = [r for r in R if (r['gid'], r['seat']) not in done]
    want = {r['gid'] for r in R}
    games = {g['id']: g for g in load_games(path) if g['id'] in want}
    jobs = [(games[r['gid']], r, cand) for r in R]
    print(len(jobs), 'seats to play', flush=True)
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'a', encoding='utf-8') as fh:
        for x in ex.map(_play, jobs):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    print('done', flush=True)
