

# =====================================================================================
# P2: day planner from day _P2_CFG['start_day'] to day 28 (day 29 stays with the final-day
# controller).  At dawn it lists every job on the board (feed/care/collect/harvest animals;
# water/fertilize/harvest/replant crops), sizes the crew, and routes all units with an open
# vehicle-routing heuristic (regret insertion + 2-opt + relocate).  Units follow their tours
# closed-loop (stale jobs are skipped, free units pick up leftovers).  The chassis keeps its
# SELL orders; hires, seeds and inputs are ours.
# =====================================================================================
import collections, time
_P2_CFG = __P2CFG__
_P2_STATE = {}
_P2_REPORT = dict(days=0, hires=0, visits=0, done_ops=0, skipped_ops=0, left_visits=0, bought_wheat=0, bought_fert=0,
                  seeds=0, errors=0, last_error='', plan_ms=0)
_P2_CROP = {  # first_yield_day, max_yield_day, interval, max_yield, ongoing, seed
    'WHEAT': (2, 4, 0, 6, False, 10), 'CARROT': (2, 3, 0, 4, False, 20), 'TOMATO': (8, 8, 1, 4, True, 50),
    'STRAWBERRY': (10, 10, 2, 4, True, 100), 'MELON': (10, 12, 0, 6, False, 80)}
_P2_ANIMAL = {'GOOSE': (4, 1, 4, 'EGG'), 'COW': (8, 2, 6, 'MILK'), 'SHEEP': (6, 3, 6, 'WOOL')}  # first, interval, max_held, product
_P2_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_P2_MOVES = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}


def _p2_d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _p2_toward(p, q):
    if p[0] != q[0]: return ['EAST' if q[0] > p[0] else 'WEST']
    if p[1] != q[1]: return ['SOUTH' if q[1] > p[1] else 'NORTH']
    return None


def _p2_price(obs, item):
    return max(1, int(obs['market']['prices'].get(item, 1)))


def _p2_crop_plan(obs, st, day, pos, prev):
    """Crop to plant on an empty tile today, or None."""
    cfg = _P2_CFG
    last = {'WHEAT': 26, 'CARROT': 26, 'TOMATO': cfg.get('tomato_last_day', 17)}
    shops = obs['town']['unlocked_shops']
    tom_shops = sum(s in ('PIZZA_SHOP', 'FARMERS_MARKET') for s in shops)
    if cfg.get('tomato') and day <= last['TOMATO'] and tom_shops >= cfg.get('tomato_min_shops', 2):
        if st['tomatoes_planted'] + st['plan_tom_today'] < cfg['tomato_n'][min(tom_shops, 3)]:
            st['plan_tom_today'] += 1
            return 'TOMATO'
    if day >= cfg.get('carrot_from_day', 23) and day <= last['CARROT']:
        return 'CARROT'
    if day <= last['WHEAT']:
        return 'WHEAT'
    return None


def _p2_visits(obs, st, day):
    """Today's visits: dict(pos, ops=[op...], prio, feed, fert, seed) built from the board."""
    player = st['player']; farm = obs['farms'][player]
    cfg = _P2_CFG
    fert_stock = int(obs['private']['shed'].get('FERTILIZER', 0))
    visits = []
    st['plan_tom_today'] = 0
    for y in range(10):
        for x in range(10):
            t = farm['tiles'][y][x]
            if t == 'LOCKED': continue
            pos = (x, y)
            if t is None:
                if pos in _P2_ACCESS and not cfg.get('plant_access'): continue
                if not cfg.get('plant_empty', True): continue
                crop = _p2_crop_plan(obs, st, day, pos, None)
                if crop:
                    visits.append(dict(pos=pos, ops=['PLANT:' + crop, 'WATER'], prio=2, feed=0, fert=0, seed=crop))
                continue
            if not isinstance(t, dict): continue
            kind = t.get('kind')
            if kind == 'WEED':
                crop = _p2_crop_plan(obs, st, day, pos, None) if cfg.get('dig_weeds', True) else None
                if crop:
                    visits.append(dict(pos=pos, ops=['DIG', 'PLANT:' + crop, 'WATER'], prio=3, feed=0, fert=0, seed=crop))
                continue
            if t.get('animal'):
                a = t['animal']; first, itv, maxh, prod = _P2_ANIMAL[a]
                since = day + 1 - int(t['placed_day']) - first
                prod_today = since >= 0 and since % itv == 0
                ops = []
                units = int(t.get('yield_units', 0) or 0)
                pend = int(t.get('pending_care_bonus', 0) or 0)
                gain = (1 + pend) if prod_today else 0
                if units > 0 and (units + gain > maxh or units >= cfg.get('animal_harvest_at', {}).get(a, 2) or day >= 28):
                    ops.append('HARVEST')
                unfed = int(t.get('consecutive_unfed', 0) or 0)
                must = unfed >= 1
                feed = must or prod_today or cfg.get('feed_daily', {}).get(a, True)
                care_ok = feed
                if feed:
                    ops.append('FEED')
                    if cfg.get('care', True) and day < 28:
                        ops.append('CARE')
                if t.get('fertilizer_available') and cfg.get('collect', True):
                    ops.append('COLLECT_FERTILIZER')
                if ops:
                    visits.append(dict(pos=pos, ops=ops, prio=0 if must else 1, feed=int('FEED' in ops), fert=0, seed=None))
                continue
            if kind != 'PLANT':
                continue
            crop = t['crop']; fyd, myd, itv, maxy, ongoing, _ = _P2_CROP[crop]
            age = day - int(t['planted_day'])
            units = int(t.get('yield_units', 0) or 0)
            unw = int(t.get('consecutive_unwatered', 0) or 0)
            fert_ok = int(t.get('fertilized_until_day', -1)) >= day
            ops = []
            if not ongoing:
                ws = (myd + 1) // 2
                decaying = day >= int(t['planted_day']) + myd + 1
                harvest_age = cfg.get('harvest_age', {}).get(crop, myd)
                if decaying:
                    ops = ['HARVEST']
                else:
                    in_win = ws <= age <= myd
                    if in_win and cfg.get('fertilize_grain') and not fert_ok and crop in ('WHEAT', 'CARROT') and age == ws and fert_stock > 0:
                        ops.append('FERTILIZE')
                    if in_win or unw >= 1:
                        ops.append('WATER')
                    if age >= harvest_age and units > 0:
                        ops.append('HARVEST')
                if 'HARVEST' in ops:
                    crop2 = _p2_crop_plan(obs, st, day, pos, crop)
                    if crop2:
                        ops += ['PLANT:' + crop2, 'WATER']
                if ops:
                    seed = next((o.split(':')[1] for o in ops if o.startswith('PLANT:')), None)
                    visits.append(dict(pos=pos, ops=ops, prio=0 if (unw >= 1 or decaying) else 1, feed=0,
                                       fert=int('FERTILIZE' in ops), seed=seed))
                continue
            # ongoing crops
            since = day + 1 - int(t['planted_day']) - fyd
            pcount = since // itv + 1 if since >= 0 and since % itv == 0 else 0
            prod_today = since >= 0 and since % itv == 0 and pcount <= maxy
            done = int(t.get('max_lifespan_step', -1)) >= 0
            gain = 2 if prod_today else 0
            if units > 0 and (done or units + gain > maxy or day >= 28 or units >= cfg.get('ongoing_harvest_at', 3)):
                ops.append('HARVEST')
            if done and units == 0 and not ops:
                if cfg.get('dig_done', True):
                    crop2 = _p2_crop_plan(obs, st, day, pos, crop)
                    if crop2:
                        visits.append(dict(pos=pos, ops=['DIG', 'PLANT:' + crop2, 'WATER'], prio=3, feed=0, fert=0, seed=crop2))
                continue
            if not done:
                if prod_today and cfg.get('fertilize_ongoing', True) and not fert_ok and fert_stock > 0:
                    ops.append('FERTILIZE')
                if prod_today or unw >= 1 or (age == 0):
                    ops.append('WATER')
            if ops:
                visits.append(dict(pos=pos, ops=ops, prio=0 if unw >= 1 else 1, feed=0, fert=int('FERTILIZE' in ops), seed=None))
    return visits


def _p2_tape_jobs(player, day):
    """Simulate the native tape for one day: per step, positions of the farmer and native hands (hires spawn on the
    least-occupied shed-access tile), recording every non-move command as (step, unit, pos, cmd)."""
    native = _IMPL.chassis.players[player]
    tape = _IMPL.chassis.routes[native['route']]
    pos = [(4, 4)]
    out = []; hires = []
    for t in range(day * 24, min((day + 1) * 24, len(tape))):
        a = tape[t] or {}
        cmds = [a.get('farmer') or ['PASS']] + list(a.get('hands') or [])
        for u in range(len(pos)):
            c = cmds[u] if u < len(cmds) else ['PASS']
            if not c: continue
            if c[0] in _P2_MOVES:
                dx, dy = _P2_MOVES[c[0]]; x, y = pos[u]; nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10: pos[u] = (nx, ny)
            elif c[0] != 'PASS':
                out.append((t, u, pos[u], list(c)))
        for o in a.get('market') or []:
            if o and o[0] == 'HIRE':
                occ = {q: 0 for q in _P2_ACCESS}
                for p in pos:
                    if p in occ: occ[p] += 1
                sp = sorted(occ.items(), key=lambda kv: (kv[1], _P2_ACCESS.index(kv[0])))[0][0]
                pos.append(sp); hires.append(t)
    return out, hires


def _p2_visits_tape(obs, st, day):
    """Today's visits from the native tape's own commands (grouped per tile in time order), plus our policy's
    visits for animals and plants the tape does not touch today (layer-owned stock, e.g. SE sheep)."""
    player = st['player']; farm = obs['farms'][player]
    jobs, hires = _p2_tape_jobs(player, day)
    st['tape_hires'] = len(hires)
    per_tile = collections.OrderedDict()
    for t, u, p, c in jobs:
        op = c[0]
        if op in ('PICKUP', 'DROP'): continue
        if op == 'PLACE':
            if len(c) > 1 and c[1] in ('COW', 'SHEEP', 'GOOSE'):
                continue   # animal placement: rare after day 15, skipped
            continue
        key = op if op != 'PLANT' else 'PLANT:' + c[1]
        per_tile.setdefault(p, []).append(key)
    visits = []
    for p, ops in per_tile.items():
        x, y = p; t = farm['tiles'][y][x]
        if t == 'LOCKED': continue
        feed = ops.count('FEED'); fert = ops.count('FERTILIZE')
        seed = next((o.split(':')[1] for o in ops if o.startswith('PLANT:')), None)
        unw = int(t.get('consecutive_unwatered', 0) or 0) if isinstance(t, dict) else 0
        unf = int(t.get('consecutive_unfed', 0) or 0) if isinstance(t, dict) else 0
        prio = 0 if (unw >= 1 and 'WATER' in ops) or (unf >= 1 and 'FEED' in ops) else 1
        visits.append(dict(pos=p, ops=ops, prio=prio, feed=feed, fert=fert, seed=seed, src='tape'))
    covered = set(per_tile)
    # our policy for everything the tape leaves alone today
    own = _p2_visits(obs, st, day)
    for v in own:
        if v['pos'] in covered: continue
        x, y = v['pos']; t = farm['tiles'][y][x]
        # only stock that needs care to survive/produce (animals, planted crops), not new plantings
        if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED'): continue
        v['src'] = 'own'
        visits.append(v)
    return visits


def _p2_route_time(start, t0, tour):
    t = t0; p = start; h = False
    for v in tour:
        t += _p2_d(p, v['pos']) + len(v['ops']); p = v['pos']
        h = h or ('HARVEST' in v['ops'])
    if h and _P2_CFG.get('deliver_plan', False):
        t += min(_p2_d(p, a) for a in _P2_ACCESS) + 1
    return t


def _p2_two_opt(start, tour):
    if len(tour) < 3: return tour
    def L(ts):
        p = start; s = 0
        for v in ts: s += _p2_d(p, v['pos']); p = v['pos']
        return s
    best = tour[:]; bl = L(best); improved = True
    while improved:
        improved = False
        for i in range(len(best) - 1):
            for j in range(i + 1, len(best)):
                c = best[:i] + best[i:j + 1][::-1] + best[j + 1:]
                cl = L(c)
                if cl < bl: best, bl, improved = c, cl, True
    return best


def _p2_assign(units, visits, end):
    """Sweep heuristic: visits in angular order around the shed are cut into open routes (2-opt each) that
    fit the day; routes go to units in order.  Several start angles are tried; the plan leaving the least
    critical work undone (then fewest leftover ops, then least time) wins.  Leftovers are then re-inserted
    wherever they still fit."""
    import math
    cx, cy = 4.5, 4.5
    ang = sorted(visits, key=lambda v: math.atan2(v['pos'][1] - cy, v['pos'][0] - cx))
    best = None
    nstarts = _P2_CFG.get('sweep_starts', 8)
    for s0 in range(0, len(ang), max(1, len(ang) // nstarts) if ang else 1):
        order = ang[s0:] + ang[:s0]
        tours = [[] for _ in units]; ui = 0; left = []
        for v in order:
            placed = False
            while ui < len(units):
                cand = _p2_two_opt(units[ui]['start'], tours[ui] + [v])
                if _p2_route_time(units[ui]['start'], units[ui]['t0'], cand) <= end:
                    tours[ui] = cand; placed = True; break
                if not tours[ui]:
                    break
                ui += 1
            if not placed: left.append(v)
        # re-insert leftovers anywhere they fit (cheapest)
        still = []
        for v in sorted(left, key=lambda v: v['prio']):
            bestins = None
            for uj, u in enumerate(units):
                tour = tours[uj]; base = _p2_route_time(u['start'], u['t0'], tour)
                for k in range(len(tour) + 1):
                    tt = _p2_route_time(u['start'], u['t0'], tour[:k] + [v] + tour[k:])
                    if tt <= end and (bestins is None or tt - base < bestins[0]): bestins = (tt - base, uj, k)
            if bestins is None: still.append(v)
            else: tours[bestins[1]].insert(bestins[2], v)
        crit = sum(1 for v in still if v['prio'] <= 1)
        score = (crit, sum(len(v['ops']) for v in still), sum(_p2_route_time(u['start'], u['t0'], t) for u, t in zip(units, tours)))
        if best is None or score < best[0]:
            best = (score, tours, still)
        if len(ang) == 0: break
    return best[1], best[2]


def _p2_spawns(farm, n_new):
    occ = {a: 0 for a in _P2_ACCESS}
    allpos = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
    for p in allpos:
        if p in occ: occ[p] += 1
    out = []
    for _ in range(n_new):
        best = sorted(occ.items(), key=lambda kv: (kv[1], _P2_ACCESS.index(kv[0])))[0][0]
        out.append(best); occ[best] += 1
    return out


def _p2_plan_day(obs, st, day):
    player = st['player']; farm = obs['farms'][player]
    visits = _p2_visits_tape(obs, st, day) if _P2_CFG.get('jobs') == 'tape' else _p2_visits(obs, st, day)
    cfg = _P2_CFG
    t_start = time.perf_counter()
    best = None
    lo = max(1, cfg.get('min_units', 5)); hi = cfg['max_units']
    for n_units in range(lo, hi + 1):
        spawns = _p2_spawns(farm, n_units - 1)
        units = [dict(start=tuple(farm['farmer']), t0=1)] + [dict(start=s, t0=2) for s in spawns]
        tours, left = _p2_assign(units, [dict(v, ops=list(v['ops'])) for v in visits], 23)
        crit = sum(1 for v in left if v['prio'] <= 1)
        opt = sum(len(v['ops']) for v in left if v['prio'] >= 2)
        best = (units, tours, left)
        if crit == 0 and opt <= cfg.get('opt_slack', 6):
            break
    units, tours, left = best
    while len(units) > 1 and not tours[-1]:
        units.pop(); tours.pop()
    _P2_REPORT['plan_ms'] += int((time.perf_counter() - t_start) * 1000)
    st['day_plan'] = dict(day=day, units=units, tours=tours, left=left)
    st['hires_wanted'] = len(units) - 1
    _P2_REPORT['visits'] += len(visits); _P2_REPORT['left_visits'] += len(left)
    need_w = sum(v['ops'].count('FEED') for tr in tours for v in tr)
    need_f = sum(v['ops'].count('FERTILIZE') for tr in tours for v in tr)
    seeds = collections.Counter(o.split(':')[1] for tr in tours for v in tr for o in v['ops'] if o.startswith('PLANT:'))
    return need_w, need_f, seeds


def _p2_unit_cmd(obs, st, actor, tour, day):
    """Command for one unit following its tour closed-loop."""
    player = st['player']; farm = obs['farms'][player]; private = obs['private']
    pos = tuple(farm['farmer']) if actor == 0 else tuple(farm['hands'][actor - 1])
    inv = private['inventories'][actor] if actor < len(private['inventories']) else {}
    ld = st['loaded'].setdefault(actor, {})
    # loading at the shed before leaving
    if not ld.get('done'):
        need_w = sum(v['ops'].count('FEED') for v in tour) - int(inv.get('WHEAT', 0))
        need_f = sum(v['ops'].count('FERTILIZE') for v in tour) - int(inv.get('FERTILIZER', 0))
        if (need_w > 0 or need_f > 0) and pos in _P2_ACCESS:
            if need_w > 0 and not ld.get('w'):
                ld['w'] = 1
                have = int(private['shed'].get('WHEAT', 0)) - st['claims'].get('WHEAT', 0)
                if have > 0:
                    q = min(have, need_w); st['claims']['WHEAT'] = st['claims'].get('WHEAT', 0) + q
                    return ['PICKUP', 'WHEAT', q]
            if need_f > 0 and not ld.get('f'):
                ld['f'] = 1
                have = int(private['shed'].get('FERTILIZER', 0)) - st['claims'].get('FERTILIZER', 0)
                if have > 0:
                    q = min(have, need_f); st['claims']['FERTILIZER'] = st['claims'].get('FERTILIZER', 0) + q
                    return ['PICKUP', 'FERTILIZER', q]
        ld['done'] = 1
    while tour:
        v = tour[0]
        if pos != v['pos']:
            return _p2_toward(pos, v['pos'])
        # at the tile: next valid op
        t = farm['tiles'][pos[1]][pos[0]]
        while v['ops']:
            op = v['ops'][0]
            ok = False
            if op == 'WATER':
                ok = isinstance(t, dict) and t.get('kind') == 'PLANT' and not t.get('watered_today')
            elif op == 'HARVEST':
                ok = isinstance(t, dict) and int(t.get('yield_units', 0) or 0) > 0 and (t.get('animal') or day - int(t.get('planted_day', day)) >= _P2_CROP.get(t.get('crop'), (0,))[0])
            elif op == 'FERTILIZE':
                ok = isinstance(t, dict) and t.get('kind') == 'PLANT' and int(inv.get('FERTILIZER', 0)) > 0
            elif op == 'FEED':
                ok = isinstance(t, dict) and t.get('animal') and not t.get('fed_today') and int(inv.get('WHEAT', 0)) > 0
            elif op == 'CARE':
                ok = isinstance(t, dict) and t.get('animal') and not t.get('cared_today')
            elif op == 'COLLECT_FERTILIZER':
                ok = isinstance(t, dict) and t.get('animal') and t.get('fertilizer_available')
            elif op == 'DIG':
                ok = isinstance(t, dict) and not t.get('animal')
            elif op.startswith('PLANT:'):
                crop = op.split(':')[1]
                ok = t is None and int(private['seeds'].get(crop, 0)) - st['seed_claims'].get(crop, 0) > 0
                if ok:
                    st['seed_claims'][crop] = st['seed_claims'].get(crop, 0) + 1
            v['ops'].pop(0)
            if ok:
                _P2_REPORT['done_ops'] += 1
                if op.startswith('PLANT:'): return ['PLANT', op.split(':')[1]]
                return [op]
            _P2_REPORT['skipped_ops'] += 1
            # a skipped DIG/PLANT invalidates the following PLANT/WATER only if the tile is not in the right state;
            # re-read the tile (unchanged) and continue
        tour.pop(0)
        if not tour:
            plan = st.get('day_plan') or {}
            left = plan.get('left') or []
            step = int(obs['step']); rem = 23 - step % 24
            cands = [v for v in left if _p2_d(pos, v['pos']) + len(v['ops']) <= rem and not any(o.startswith('PLANT:') for o in v['ops'])
                     and not ('FEED' in v['ops'] and int(inv.get('WHEAT', 0)) <= 0) and not ('FERTILIZE' in v['ops'] and int(inv.get('FERTILIZER', 0)) <= 0)]
            if cands:
                v = min(cands, key=lambda v: (v['prio'], _p2_d(pos, v['pos'])))
                left.remove(v); tour.append(v)
    goods = sum(int(n) for k, n in inv.items() if k not in ('WHEAT', 'FERTILIZER') and int(n) > 0)
    if goods > 0 and _P2_CFG.get('deliver', True):
        home = min(_P2_ACCESS, key=lambda a: _p2_d(pos, a))
        rem = 23 - int(obs['step']) % 24
        if _p2_d(pos, home) + 1 <= rem + 1:
            return _p2_toward(pos, home) or ['DROP']
    return ['PASS']


_P2_PARENT = agent
def agent(observation, configuration=None):
    action = _P2_PARENT(observation, configuration)
    try:
        return _p2_apply(observation, action)
    except Exception as ex:
        _P2_REPORT['errors'] += 1; _P2_REPORT['last_error'] = repr(ex)[:300]
        return action


def _p2_apply(obs, action):
    if not isinstance(action, dict): return action
    step = int(obs['step']); player = int(obs['player']); day, hour = divmod(step, 24)
    st = _P2_STATE.get(player)
    if st is None or step <= st['last']:
        st = _P2_STATE[player] = dict(last=step, player=player, day=-1, tomatoes_planted=0, plan_tom_today=0)
        if step > 0:
            for k in _P2_REPORT: _P2_REPORT[k] = 0 if k != 'last_error' else ''
    st['last'] = step
    if day < _P2_CFG['start_day'] or step >= 696:
        return action
    farm = obs['farms'][player]; private = obs['private']
    parent_market = list(action.get('market') or [])
    market = []
    # keep the chassis' sales, but never sell today's feed/fertilizer needs
    for o in parent_market:
        if o and o[0] == 'SELL':
            market.append(list(o))
    if st['day'] != day:
        st['day'] = day; st['loaded'] = {}; st['claims'] = {}; st['seed_claims'] = {}
        need_w, need_f, seeds = _p2_plan_day(obs, st, day)
        _P2_REPORT['days'] += 1
        st['need_w'] = need_w; st['need_f'] = need_f
        # inputs: buy what the shed lacks now (available from the next step)
        shed = private['shed']
        orders = []
        dw = need_w + _P2_CFG.get('wheat_margin', 2) - int(shed.get('WHEAT', 0))
        if dw > 0: orders.append(['BUY_PRODUCT', 'WHEAT', dw]); _P2_REPORT['bought_wheat'] += dw
        df = need_f - int(shed.get('FERTILIZER', 0))
        if df > 0 and _P2_CFG.get('buy_fert', True): orders.append(['BUY_PRODUCT', 'FERTILIZER', df]); _P2_REPORT['bought_fert'] += df
        for crop, n in seeds.items():
            have = int(private['seeds'].get(crop, 0))
            if n > have: orders.append(['BUY_SEED', crop, n - have]); _P2_REPORT['seeds'] += n - have
        hires = [['HIRE'] for _ in range(st['hires_wanted'])]
        st['pending_orders'] = hires + orders
        tom = sum(1 for tr in st['day_plan']['tours'] for v in tr for o in v['ops'] if o == 'PLANT:TOMATO')
        st['tomatoes_planted'] += tom
    # own selling: products go out as soon as they are in the shed; inputs above tomorrow's reserve too
    shed = private['shed']
    animals = sum(1 for row in farm['tiles'] for t in row if isinstance(t, dict) and t.get('animal'))
    feeds_left = sum(v['ops'].count('FEED') for tr in (st.get('day_plan') or {}).get('tours', []) for v in tr)
    carried_w = sum(int((inv or {}).get('WHEAT', 0)) for inv in (private.get('inventories') or []))
    keep_w = max(0, feeds_left - carried_w) + (animals if hour < 20 else min(animals, _P2_CFG.get('dawn_wheat', 8))) + _P2_CFG.get('wheat_margin', 2)
    keep_f = _P2_CFG.get('fert_keep', 10)
    market = []
    if not _P2_CFG.get('chassis_sales'):
        for item, n in shed.items():
            n = int(n)
            if n <= 0 or item in ('COW', 'SHEEP', 'GOOSE'): continue
            if item == 'WHEAT': n -= keep_w
            elif item == 'FERTILIZER': n -= keep_f
            if n > 0: market.append(['SELL', item, n])
    else:
        for o in parent_market:
            if o and o[0] == 'SELL': market.append(list(o))
    market.sort(key=lambda o: -int(o[2]))
    # pending orders: sales keep their slots; hires take the remaining room, then inputs; the rest waits
    pend = st.get('pending_orders') or []
    hires = [o for o in pend if o[0] == 'HIRE']; buys = [o for o in pend if o[0] != 'HIRE']
    market = market[:10]
    room = 10 - len(market)
    take_h = hires[:room]; room -= len(take_h)
    take_b = buys[:room]
    st['pending_orders'] = hires[len(take_h):] + buys[len(take_b):]
    _P2_REPORT['hires'] += len(take_h)
    market = take_h + market + take_b
    # unit commands (seed and shed claims are per step)
    st['seed_claims'] = {}; st['claims'] = {}
    plan = st.get('day_plan')
    n = 1 + len(farm['hands'])
    cmds = [['PASS'] for _ in range(n)]
    if plan and plan['day'] == day:
        for actor in range(n):
            if actor < len(plan['tours']):
                cmds[actor] = _p2_unit_cmd(obs, st, actor, plan['tours'][actor], day) or ['PASS']
    out = dict(action); out['farmer'] = cmds[0]; out['hands'] = cmds[1:]; out['market'] = market
    return out


agent.telemetry = _P2_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
