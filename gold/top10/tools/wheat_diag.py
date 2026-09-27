"""Crop/labour diagnostics per farm and day: plantings, harvests (age, units, fertilized), waterings, hires, land.
usage: wheat_diag.py rec  games.jsonl.gz refs.jsonl out.jsonl [max]          # the recorded game replayed (both tapes)
       wheat_diag.py cand games.jsonl.gz refs.jsonl cand.py out.jsonl [max]  # candidate vs the repaired elite (elite_gate set-up)
Each row: gid, seat, team, m (cand mode), and per side ('elite', 'us' in cand mode; 'elite', 'opp' in rec mode) a list of
30 day records: plant {crop@Q: n}, harv {crop: [[age, units, fert], ...]}, water {crop: n}, fert {crop: n}, hires, hire$,
land [quadrant], acts (non-PASS unit actions), tiles {crop: n} at the end of the day, sold {item: units}, bought {item: units}.
"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
Q = lambda x, y: ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')


def _instrument(K):
    """Wrap engine functions; returns (recs keyed by id(farm), FARMS holder, restore fn)."""
    recs = collections.defaultdict(lambda: [dict(plant=collections.Counter(), harv=collections.defaultdict(list),
                                                 water=collections.Counter(), fert=collections.Counter(), hires=0, hire_cost=0,
                                                 land=[], acts=0, units=0, sold=collections.Counter(), sold_d=collections.Counter(),
                                                 bought=collections.Counter(), tiles={}) for _ in range(30)])
    STEP = [0]; FARMS = [None, None]; PRIV = {}
    ou = K._apply_unit_action
    def unit(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity=100):
        r = recs[id(farm)][min(day, 29)]
        op = action[0] if isinstance(action, list) and action else None
        pos = K._farmer_position(farm, idx)
        if op is not None and op != 'PASS':
            r['acts'] += 1
        tile0 = None
        if pos is not None and op in ('HARVEST', 'PLANT', 'WATER', 'FERTILIZE'):
            t = farm['tiles'][pos[1]][pos[0]]
            tile0 = dict(t) if isinstance(t, dict) else t
        ou(farm, private, idx, action, board_size, day, turns_per_day, shed_capacity)
        if tile0 is None and op != 'PLANT':
            return
        t1 = farm['tiles'][pos[1]][pos[0]]
        if op == 'PLANT' and tile0 is None and isinstance(t1, dict) and t1.get('kind') == 'PLANT':
            r['plant'][t1['crop'] + '@' + Q(pos[0], pos[1])] += 1
        elif op == 'HARVEST' and isinstance(tile0, dict) and tile0.get('kind') == 'PLANT':
            cd = K.CROPS[tile0['crop']]
            if not cd['ongoing'] and t1 is None:
                r['harv'][tile0['crop']].append([day - tile0['planted_day'], tile0['yield_units'],
                                                 int(tile0.get('fertilized_until_day', -1) >= day)])
            elif cd['ongoing'] and isinstance(t1, dict) and t1.get('yield_units', 0) == 0 and tile0.get('yield_units', 0) > 0:
                r['harv'][tile0['crop']].append([day - tile0['planted_day'], tile0['yield_units'], 1])
        elif op == 'WATER' and isinstance(tile0, dict) and tile0.get('kind') == 'PLANT' and not tile0['watered_today']:
            r['water'][tile0['crop']] += 1
        elif op == 'FERTILIZE' and isinstance(tile0, dict) and tile0.get('kind') == 'PLANT' and isinstance(t1, dict) \
                and t1.get('fertilized_until_day', -1) != tile0.get('fertilized_until_day', -1):
            r['fert'][tile0['crop']] += 1
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if farm['money'] != m0:
            r = recs[id(farm)][min(STEP[0] // 24, 29)]; r['hires'] += 1; r['hire_cost'] += m0 - farm['money']
    ol = K._do_buy_land
    def land(farm, bs):
        n0 = len(farm['unlocked_quadrants']); ol(farm, bs)
        if len(farm['unlocked_quadrants']) != n0:
            recs[id(farm)][min(STEP[0] // 24, 29)]['land'].append(farm['unlocked_quadrants'][-1])
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok:
            r = recs[id(farm)][min(STEP[0] // 24, 29)]
            if op == 'SELL': r['sold'][item] += 1; r['sold_d'][item] += price
            elif op == 'BUY_PRODUCT': r['bought'][item] += 1
        return ok
    opm = K._process_market
    def pm(state, env):
        STEP[0] = int(state[0].observation.step)
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        for i in (0, 1):
            PRIV[id(state[i].observation.private)] = id(FARMS[i])
        for f in FARMS:
            recs[id(f)][min(STEP[0] // 24, 29)]['units'] += len(f['hands']) + 1
        return opm(state, env)
    oe = K._end_of_day
    def eod(state, env, day):
        for f in state[0].observation.farms:
            c = collections.Counter()
            for y, row in enumerate(f['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict):
                        c[t.get('crop') or t.get('animal') or t.get('kind')] += 1
            recs[id(f)][min(day, 29)]['tiles'] = dict(c)
        return oe(state, env, day)
    od = K._drop_inventories_to_shed
    def drop(private, capacity):
        shed0 = sum(int(v) for v in private['shed'].values())
        car = collections.Counter()
        for inv in private['inventories']:
            for k, v in inv.items(): car[k] += int(v)
        sh = dict(private['shed'])
        od(private, capacity)
        lost = {}
        for k, v in car.items():
            got = int(private['shed'].get(k, 0)) - int(sh.get(k, 0))
            if v - got > 0: lost[k] = v - got
        fid = PRIV.get(id(private))
        if fid is not None:
            recs[fid][min(STEP[0] // 24, 29)]['night'] = dict(shed=shed0, carried=sum(car.values()), lost=lost,
                                                           shed_items={k: int(v) for k, v in sh.items() if v})
    K._drop_inventories_to_shed = drop
    K._apply_unit_action = unit; K._do_hire = hire; K._do_buy_land = land; K._commit_unit = commit; K._process_market = pm; K._end_of_day = eod
    def restore():
        K._drop_inventories_to_shed = od
        K._apply_unit_action = ou; K._do_hire = oh; K._do_buy_land = ol; K._commit_unit = oc; K._process_market = opm; K._end_of_day = oe
    return recs, FARMS, restore


def _clean(days):
    out = []
    for r in days:
        out.append(dict(plant=dict(r['plant']), harv=dict(r['harv']), water=dict(r['water']), fert=dict(r['fert']), hires=r['hires'],
                        hire_cost=r['hire_cost'], land=r['land'], acts=r['acts'], units=r['units'], sold=dict(r['sold']),
                        sold_d=dict(r['sold_d']), bought=dict(r['bought']), tiles=r['tiles'], night=r.get('night')))
    return out


def _rec(t):
    import lean, pinned4
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref = t
    s = ref['seat']
    recs, FARMS, restore = _instrument(K)
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned4._tape(d['acts'], 0), pinned4._tape(d['acts'], 1)])
    finally:
        restore()
    return dict(gid=ref['gid'], seat=s, team=ref['team'], opp=ref.get('opp'), r=r['r'], rec=d['rewards'],
                elite=_clean(recs[id(FARMS[s])]), other=_clean(recs[id(FARMS[1 - s])]))


def _cand(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    recs, FARMS, restore = _instrument(K)
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        restore(); K._end_of_day = orig
    tape, cd = r['r'][s], r['r'][1 - s]
    return dict(gid=ref['gid'], seat=s, team=ref['team'], cand=cand, tape=tape, us=cd,
                m=(cd - tape) if tape is not None and cd is not None else None,
                elite=_clean(recs[id(FARMS[s])]), other=_clean(recs[id(FARMS[1 - s])]))


if __name__ == '__main__':
    from eval_elite_routes import load_games
    mode = sys.argv[1]
    path, refs = sys.argv[2], sys.argv[3]
    if mode == 'rec':
        out = sys.argv[4]; maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
    else:
        cand, out = sys.argv[4], sys.argv[5]; maxg = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
    R = [json.loads(l) for l in open(refs, encoding='utf-8')][:maxg]
    ids = {r['gid'] for r in R}
    games = {g['id']: g for g in load_games(path) if g['id'] in ids}
    jobs = [(games[r['gid']], r) if mode == 'rec' else (games[r['gid']], r, cand) for r in R]
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(_rec if mode == 'rec' else _cand, jobs):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
    print('done', len(jobs), 'wall %.0fs' % (time.time() - t0))
