"""Replay recorded games (both seats on their recorded actions) with per-day hooks: money, market $/units per product,
hires, plantings, tiles, verbs, holdings, day 22+ per-step sales, leftovers at the end.
usage: replay_days.py out.jsonl team file1.json [file2.json ...]   (files: one-game lists, e.g. live191.json.d/*.json)
"""
import sys, os, json, collections, time
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')

def tape(acts, p):
    def f(obs, cfg=None):
        t = obs['step']
        a = acts[t + 1][p] if t + 1 < len(acts) else None
        return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
    return f

def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, team = t
    d = json.load(open(path, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index(team) if team in names else 0
    days = [[], []]
    mk = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    steps = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    VB = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    FARMS = [None, None]; STEP = [0]; FINAL = [None, None]
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
    def snap_hold(farm, private):
        held = collections.Counter({k: v for k, v in private['shed'].items() if v})
        for inv in private.get('inventories', []) or []:
            for k, v in (inv or {}).items():
                if v: held[k] += v
        ripe = collections.Counter()
        for row in farm['tiles']:
            for tile in row:
                if isinstance(tile, dict) and (tile.get('crop') or tile.get('animal')) and tile.get('yield_units'):
                    ripe[tile.get('crop') or tile.get('animal')] += tile['yield_units']
        return dict(held), dict(ripe)
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = int(K.get(state[0].observation, 'step', 0))
        out = opm(state, env)
        if STEP[0] >= 718:
            for pid, farm in enumerate(state[0].observation.farms):
                h, r = snap_hold(farm, state[pid].observation.private)
                FINAL[pid] = dict(held=h, ripe=r)
        return out
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None and farm['money'] != m0:
            i = 0 if farm is FARMS[0] else 1
            mk[i][STEP[0] // 24]['hire$'] += m0 - farm['money']; mk[i][STEP[0] // 24]['hires'] += 1
    oau = K._apply_unit_action
    MV = set(K.FARMER_MOVES)
    def au(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        if FARMS[0] is not None and isinstance(action, list) and action:
            i = 0 if farm is FARMS[0] else 1
            op = action[0]
            VB[i][day]['MOVE' if op in MV else str(op)] += 1
        return oau(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
    oe = K._end_of_day
    def eod(state, env, day):
        obs0 = state[0].observation
        pre = []
        for pid, farm in enumerate(obs0.farms):
            c = collections.Counter(); planted = collections.Counter()
            for row in farm['tiles']:
                for tile in row:
                    if isinstance(tile, dict):
                        if tile.get('crop'):
                            c[tile['crop']] += 1
                            if tile.get('planted_day') == day: planted[tile['crop']] += 1
                        elif tile.get('animal'): c[tile['animal']] += 1
                        elif tile.get('kind') == 'WEED': c['WEED'] += 1
            h, r = snap_hold(farm, state[pid].observation.private)
            pre.append(dict(day=day, money=round(farm['money']), tiles=dict(c), planted=dict(planted), held=h, ripe=r, mkt=dict(mk[pid][day])))
        out = oe(state, env, day)
        for pid, farm in enumerate(obs0.farms):
            pre[pid]['ripe_post'] = snap_hold(farm, state[pid].observation.private)[1]
            days[pid].append(pre[pid])
        return out
    K._commit_unit = commit; K._process_market = pm; K._do_hire = hire; K._apply_unit_action = au; K._end_of_day = eod
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[tape(d['acts'], 0), tape(d['acts'], 1)])
    finally:
        K._commit_unit = oc; K._process_market = opm; K._do_hire = oh; K._apply_unit_action = oau; K._end_of_day = oe
    O = 1 - P
    cv = lambda i: {str(k): dict(v) for k, v in VB[i].items()}
    sv = lambda i: {str(k): dict(v) for k, v in steps[i].items()}
    return dict(gid=d['id'], opp=names[O], us=r['r'][P], them=r['r'][O], m=r['r'][P] - r['r'][O], rec=d['rewards'][P] - d['rewards'][O],
                days_us=days[P], days_them=days[O], steps_us=sv(P), steps_them=sv(O), verbs_us=cv(P), verbs_them=cv(O),
                final_us=FINAL[P], final_them=FINAL[O], mkt29_us=dict(mk[P][29]), mkt29_them=dict(mk[O][29]))

if __name__ == '__main__':
    out, team = sys.argv[1], sys.argv[2]
    files = sys.argv[3:]
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '1'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(job, [(f, team) for f in files]):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    print('done', flush=True)
