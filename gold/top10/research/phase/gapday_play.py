"""WHEN is the gap created: sf8 (or any candidate) vs a repaired elite in its own town (elite_gate._play set-up),
with a per-day record of both farms.

usage: gapday_play.py games.jsonl.gz refs.jsonl cand.py out.jsonl [per_team] [teams|ALL]
  NPROC workers (default 2). Rows: gid, seat, team, us, elite, m, days_us / days_elite (list of 31 dicts).

Per farm and day D the row holds
  s   (snapshot at the START of day D, i.e. after the engine's end of day D-1; D = 30 is the final state before the
       last money count): money, quads, animals by kind {n, units}, plants by crop {n, units, ages}, shed goods,
       seeds, empty structures
  f   (flows during day D): sales $ / units by product, buys $ / units, seed $ by crop, animal $ by kind, hires $ / n,
       land $, max hands, effective unit ops (PLANT by crop, WATER, HARVEST units by product, FEED, CARE, COLLECT,
       FERTILIZE, DIG, moves, PASS/idle)
  q   market quotes at the snapshot.
"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
sys.path.insert(0, '/home/user/kaggriculture/gold/elite')


def _play(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()},
              shops=ref['shops'])
    orig_eod = install_town(ref['shops'])
    pinned_eod = K._end_of_day
    FARMS = [None, None]; STEP = [0]
    flows = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    snaps = [dict(), dict()]; quotes = {}

    def pid_of(farm):
        if FARMS[0] is None: return None
        return 0 if farm is FARMS[0] else (1 if farm is FARMS[1] else None)

    def snap(obs0, state, day):
        mk = obs0.market
        quotes[day] = {it: K.market_price(it, mk['inventory'][it], mk.get('params')) for it in K.PRODUCTS}
        for pid, farm in enumerate(obs0.farms):
            private = state[pid].observation.private
            an = collections.defaultdict(lambda: [0, 0]); pl = collections.defaultdict(lambda: [0, 0, 0])
            ages = collections.defaultdict(collections.Counter); empty = collections.Counter()
            for y, row in enumerate(farm['tiles']):
                for x, tile in enumerate(row):
                    if not isinstance(tile, dict): continue
                    if 'animal' in tile:
                        a = an[tile['animal']]; a[0] += 1; a[1] += tile.get('yield_units', 0)
                    elif tile.get('kind') == 'PLANT':
                        p = pl[tile['crop']]; p[0] += 1; p[1] += tile.get('yield_units', 0)
                        ages[tile['crop']][day - tile['planted_day']] += 1
                    else:
                        empty[str(tile.get('kind'))] += 1
            inv = collections.Counter()
            for iv in private['inventories']:
                for k, v in iv.items(): inv[k] += v
            snaps[pid][day] = dict(money=round(farm['money'], 1), quads=list(farm['unlocked_quadrants']),
                                   an={k: v for k, v in an.items()}, pl={k: v[:2] for k, v in pl.items()},
                                   ages={k: dict(v) for k, v in ages.items()}, empty=dict(empty),
                                   shed={k: v for k, v in private['shed'].items() if v},
                                   inv=dict(inv), seeds={k: v for k, v in private['seeds'].items() if v})

    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        i = pid_of(farm)
        if ok and i is not None:
            f = flows[i][STEP[0] // 24]
            if op == 'SELL': f['S$' + item] += price; f['Su' + item] += 1
            elif op == 'BUY_PRODUCT': f['B$' + item] += price; f['Bu' + item] += 1
            elif op == 'BUY_SEED': f['seed$' + item] += price
            elif op == 'BUY_ANIMAL': f['anim$' + item] += price; f['animu' + item] += 1
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; n0 = len(farm['hands']); oh(farm, private, bs, mult)
        i = pid_of(farm)
        if i is not None and len(farm['hands']) > n0:
            f = flows[i][STEP[0] // 24]; f['hire$'] += m0 - farm['money']; f['hire_n'] += 1
            f['maxhands'] = max(f['maxhands'], len(farm['hands']))
    ol = K._do_buy_land
    def land(farm, bs):
        m0 = farm['money']; ol(farm, bs)
        i = pid_of(farm)
        if i is not None and farm['money'] < m0: flows[i][STEP[0] // 24]['land$'] += m0 - farm['money']
    oa = K._apply_unit_action
    def act(farm, private, idx, action, bs, day, tpd, cap=100):
        i = pid_of(farm)
        if i is None or not isinstance(action, list) or not action:
            if i is not None: flows[i][day]['op_none'] += 1
            return oa(farm, private, idx, action, bs, day, tpd, cap)
        op = action[0]
        pos = K._farmer_position(farm, idx)
        pre = None
        if pos is not None and op not in K.FARMER_MOVES and op != 'PASS':
            t0 = farm['tiles'][pos[1]][pos[0]]
            pre = dict(t0) if isinstance(t0, dict) else t0
        r = oa(farm, private, idx, action, bs, day, tpd, cap)
        f = flows[i][day]
        if pos is None: return r
        if op in K.FARMER_MOVES: f['op_move'] += 1; return r
        if op == 'PASS': f['op_pass'] += 1; return r
        t1 = farm['tiles'][pos[1]][pos[0]]
        if op == 'PLANT':
            if pre is None and isinstance(t1, dict) and t1.get('kind') == 'PLANT': f['plant_' + t1['crop']] += 1
            else: f['op_fail'] += 1
        elif op == 'WATER':
            if isinstance(pre, dict) and not pre.get('watered_today') and isinstance(t1, dict) and t1.get('watered_today'):
                f['water'] += 1; f['water_' + t1['crop']] += 1
            else: f['op_fail'] += 1
        elif op == 'HARVEST':
            if isinstance(pre, dict) and pre.get('yield_units', 0) > 0:
                prod = pre['crop'] if pre.get('kind') == 'PLANT' else K.ANIMALS[pre['animal']]['product'] if 'animal' in pre else None
                if prod: f['hv_' + prod] += pre['yield_units']; f['hvn_' + prod] += 1
                if pre.get('kind') == 'PLANT' and not K.CROPS[pre['crop']]['ongoing']:
                    f['hvage_' + pre['crop']] += day - pre['planted_day']
            else: f['op_fail'] += 1
        elif op in ('FEED', 'CARE', 'COLLECT_FERTILIZER', 'FERTILIZE', 'DIG', 'BUILD_COOP', 'BUILD_PASTURE', 'DROP', 'PICKUP', 'PLACE'):
            ch = (pre != (dict(t1) if isinstance(t1, dict) else t1)) or op in ('DROP', 'PICKUP')
            f['op_' + op] += 1 if ch else 0
            if not ch: f['op_fail'] += 1
            if op == 'FERTILIZE' and ch and isinstance(t1, dict) and t1.get('crop'): f['fert_' + t1['crop']] += 1
            if op == 'CARE' and ch and isinstance(t1, dict): f['care_' + t1.get('animal', '?')] += 1
        else:
            f['op_other'] += 1
        return r
    opm = K._process_market
    def pm(state, env):
        return opm(state, env)
    oi = K.interpreter
    def interp(state, env):
        o = state[0].observation
        if getattr(o, 'farms', None):
            FARMS[0], FARMS[1] = o.farms[0], o.farms[1]
            STEP[0] = int(K.get(o, 'step', 0))
            if STEP[0] == 0 and 0 not in quotes: snap(o, state, 0)
        r = oi(state, env)
        if getattr(o, 'farms', None) and STEP[0] >= 718 and 30 not in quotes: snap(o, state, 30)
        return r
    def eod(state, env, day):
        r = pinned_eod(state, env, day)
        snap(state[0].observation, state, day + 1)
        return r
    K._commit_unit = commit; K._do_hire = hire; K._do_buy_land = land; K._apply_unit_action = act
    K.interpreter = interp; K._end_of_day = eod
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig_eod; K._commit_unit = oc; K._do_hire = oh; K._do_buy_land = ol
        K._apply_unit_action = oa; K.interpreter = oi; K._process_market = opm
    def days(pid, rew):
        out = []
        for D in range(31):
            rec = dict(D=D, s=snaps[pid].get(D), f=dict(flows[pid].get(D, {})))
            out.append(rec)
        out[30]['final'] = rew
        return out
    e, u = r['r'][s], r['r'][1 - s]
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    return dict(gid=ref['gid'], seat=s, team=ref['team'], cand=cand, shops=ref['shops'], elite=e, us=u, tel=tel,
                m=(u - e) if (u is not None and e is not None) else None, err=r['err'], wall=round(time.time() - t0, 1),
                q={str(k): v for k, v in quotes.items()}, days_us=days(1 - s, u), days_elite=days(s, e))


if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, cand, out = sys.argv[1:5]
    per = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
    teams = sys.argv[6] if len(sys.argv) > 6 else 'ALL'
    R = [json.loads(l) for l in open(refs, encoding='utf-8')]
    cnt = collections.Counter(); sel = []
    for r in R:
        if teams != 'ALL' and r['team'] not in teams.split(','): continue
        if cnt[r['team']] >= per: continue
        cnt[r['team']] += 1; sel.append(r)
    del R
    done = set()
    if os.environ.get('RESUME') and os.path.exists(out):
        done = {(json.loads(l)['gid'], json.loads(l)['seat']) for l in open(out, encoding='utf-8') if l.strip()}
    sel = [r for r in sel if (r['gid'], r['seat']) not in done]
    want = {r['gid'] for r in sel}
    games = {g['id']: g for g in load_games(path) if g['id'] in want}
    jobs = [(games[r['gid']], r, cand) for r in sel]
    print(len(jobs), 'seats', dict(cnt), flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'a' if done else 'w', encoding='utf-8') as fh:
        for i, x in enumerate(ex.map(_play, jobs)):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
            print(i, x['team'], x['gid'], x['seat'], 'm', x['m'], 'wall', x['wall'], 'T', round(time.time() - t0), flush=True)
