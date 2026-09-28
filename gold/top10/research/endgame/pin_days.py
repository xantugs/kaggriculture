"""Pinned live games (pinned4 set-up, candidate from step S, rival on its recorded tape) with per-day hooks, so the
endgame of a candidate can be read day by day against the recorded rival (same fields as day_led.py: us/elite).
usage: PIN_GIDS=ids.txt pin_days.py games.json S cand.py out.jsonl [team]"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')

def job(t):
    import lean, pinned4
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, team, cand, S = t
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, rref = pinned4.reference(d)
    orig = pinned4.install_pinned(S // 24, O, spawns, shops)
    pinned_eod = K._end_of_day
    days = [[], []]
    mk = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    steps = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    VB = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    FARMS = [None, None]; STEP = [0]
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
        return opm(state, env)
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None and farm['money'] != m0:
            i = 0 if farm is FARMS[0] else 1
            mk[i][STEP[0] // 24]['hire$'] += m0 - farm['money']; mk[i][STEP[0] // 24]['hires'] += 1
    def snap(farm, private, day):
        c = collections.Counter(); planted = collections.Counter(); ripe = collections.Counter()
        for row in farm['tiles']:
            for tile in row:
                if isinstance(tile, dict):
                    if tile.get('crop'):
                        c[tile['crop']] += 1; ripe[tile['crop']] += tile.get('yield_units', 0) or 0
                        if tile.get('planted_day') == day: planted[tile['crop']] += 1
                    elif tile.get('animal'):
                        c[tile['animal']] += 1; ripe[tile['animal']] += tile.get('yield_units', 0) or 0
        held = collections.Counter({k: v for k, v in private['shed'].items() if v})
        for inv in private.get('inventories', []) or []:
            for k, v in (inv or {}).items():
                if v: held[k] += v
        return c, planted, ripe, held
    def eod(state, env, day):
        obs0 = state[0].observation
        pre = []
        for pid, farm in enumerate(obs0.farms):
            c, planted, ripe, held = snap(farm, state[pid].observation.private, day)
            pre.append(dict(day=day, money=round(farm['money']), tiles=dict(c), planted=dict(planted), ripe=dict(ripe), held=dict(held), mkt=dict(mk[pid][day])))
        out = pinned_eod(state, env, day)
        for pid, farm in enumerate(obs0.farms):
            c, planted, ripe, held = snap(farm, state[pid].observation.private, day + 1)
            pre[pid]['ripe_post'] = dict(ripe)
            days[pid].append(pre[pid])
        return out
    oau = K._apply_unit_action
    MV = set(K.FARMER_MOVES)
    def au(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        if FARMS[0] is not None and isinstance(action, list) and action:
            i = 0 if farm is FARMS[0] else 1
            VB[i][day]['MOVE' if action[0] in MV else str(action[0])] += 1
        return oau(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
    K._end_of_day = eod; K._commit_unit = commit; K._process_market = pm; K._do_hire = hire; K._apply_unit_action = au
    try:
        A = lean.load(cand)
        ag = [None, None]; ag[P] = pinned4._prefixed(A, d['acts'], P, S); ag[O] = pinned4._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh; K._apply_unit_action = oau
    sv = lambda i: {str(k): dict(v) for k, v in steps[i].items()}
    cv = lambda i: {str(k): dict(v) for k, v in VB[i].items()}
    return dict(gid=d['id'], opp=names[O], us=r['r'][P], elite=r['r'][O], m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None,
                err=r['err'], days_us=days[P], days_elite=days[O], steps_us=sv(P), steps_elite=sv(O), verbs_us=cv(P), verbs_elite=cv(O),
                final_us={}, final_elite={}, mkt29_us=dict(mk[P][29]), mkt29_elite=dict(mk[O][29]))

if __name__ == '__main__':
    f, S, cand, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    want = set(int(x) for x in open(os.environ["PIN_GIDS"]).read().split())
    split = f + '.d'
    files = []
    for fn in sorted(os.listdir(split), key=lambda s: int(s.split('.')[0])):
        files.append(os.path.join(split, fn))
    jobs = []
    for p in files:
        d = json.load(open(p, encoding='utf-8'))[0]
        if d['id'] in want and team in d['info']['TeamNames']: jobs.append((p, team, cand, S))
        del d
    print(len(jobs), 'games', flush=True)
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(job, jobs):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    print('done', flush=True)
