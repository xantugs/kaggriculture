

# =====================================================================================
# P15: our own farm planner from day 15 to day 28 (day 29 stays with the final-day
# controller). Every unit is scheduled from the observed board each step: water what needs
# water, fertilize before the watering that it multiplies, harvest before caps/decay, feed
# and care animals, collect fertilizer, replant empty plots, deliver produce, and sell with a
# price-aware hold. Hires are sized to the day's work.
# =====================================================================================
_P15_CFG = __P15CFG__
_P15_STATE = {}
_P15_REPORT = dict(days=0, hires=0, errors=0, planted=0, fert=0, water=0, harvest=0, feed=0, care=0, collect=0, aharvest=0, dig=0, idle=0, sold=0)
_P15_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_P15_PROD = {'COW': 'MILK', 'SHEEP': 'WOOL', 'GOOSE': 'EGG'}
_P15_ANIM = {'GOOSE': (4, 1, 4), 'COW': (8, 2, 6), 'SHEEP': (6, 3, 6)}
# crop: first_yield_day, max_yield_day, interval, max_yield, ongoing, seed
_P15_CROP = {'WHEAT': (2, 4, 0, 6, False, 10), 'CARROT': (2, 3, 0, 4, False, 20), 'TOMATO': (8, 8, 1, 4, True, 50),
             'STRAWBERRY': (10, 10, 2, 4, True, 100), 'MELON': (10, 12, 0, 6, False, 80)}
_P15_SELLABLE = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER')


def _p15_d(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _p15_toward(p, q):
    if p[0] != q[0]:
        return ['EAST' if q[0] > p[0] else 'WEST']
    if p[1] != q[1]:
        return ['SOUTH' if q[1] > p[1] else 'NORTH']
    return None


def _p15_access(p):
    return min(_P15_ACCESS, key=lambda a: (_p15_d(p, a), _P15_ACCESS.index(a)))


def _p15_plant_ops(t, day, has_fert, want_fert=True):
    """Due operations on a live plant today, in execution order."""
    crop = t['crop']; fyd, myd, interval, maxy, ongoing, _ = _P15_CROP[crop]
    age = day - int(t['planted_day']); y = int(t.get('yield_units', 0)); fu = int(t.get('fertilized_until_day', -1))
    watered = bool(t.get('watered_today')); cu = int(t.get('consecutive_unwatered', 0))
    ops = []
    if not ongoing:
        ws = (myd + 1) // 2
        in_window = ws <= age <= myd
        # fertilize at the first window day (covers the rest of the window) before that day's watering
        if want_fert and has_fert and not watered and in_window and fu < day and y < maxy and (maxy - y) >= 2:
            ops.append('FERTILIZE')
        if not watered and (cu >= 1 or in_window):
            ops.append('WATER')
        if age >= fyd and y > 0 and (age >= myd and (watered or 'WATER' in ops)) or (age > myd and y > 0):
            ops.append('HARVEST')
        return ops
    # ongoing crops: production refreshes at the end of ages first-1, first-1+interval, ... (4 of them)
    prod_ages = [fyd - 1 + k * interval for k in range(maxy)]
    prod_today = age in prod_ages
    last_prod = prod_ages[-1]
    if want_fert and has_fert and fu < day and age <= last_prod and any(age <= a <= age + 2 for a in prod_ages) and y <= maxy - 2:
        # fertilize only on a day whose 3-day cover includes a production refresh not yet covered
        if prod_today:
            ops.append('FERTILIZE')
    need_water = (cu >= 1) or prod_today
    if not watered and need_water and age <= last_prod + 1:
        ops.append('WATER')
    nxt = 2 if (fu >= day or 'FERTILIZE' in ops) else 1
    if y > 0 and (y + (nxt if prod_today else 0) > maxy or age > last_prod or (prod_today and y >= maxy - 1)):
        ops.append('HARVEST')
    elif y >= maxy - 1 and y > 0:
        ops.append('HARVEST')
    return ops


def _p15_animal_ops(t, day, has_wheat, price, cfg):
    kind = t['animal']; fyd, interval, cap = _P15_ANIM[kind]
    y = int(t.get('yield_units', 0)); fed = bool(t.get('fed_today')); cared = bool(t.get('cared_today'))
    cuf = int(t.get('consecutive_unfed', 0))
    days_since_first = day + 1 - int(t['placed_day']) - fyd
    prod_tonight = days_since_first >= 0 and days_since_first % interval == 0
    item = _P15_PROD[kind]
    worth = price.get(item, 0) >= cfg['care_min'].get(item, 0)
    ops = []
    if not fed and has_wheat and (cuf >= 1 or worth or prod_tonight):
        ops.append('FEED')
    if not cared and worth and (fed or 'FEED' in ops):
        ops.append('CARE')
    if t.get('fertilizer_available'):
        ops.append('COLLECT_FERTILIZER')
    pend = int(t.get('pending_care_bonus', 0)) + (1 if 'CARE' in ops else 0)
    gain = (1 + pend) if prod_tonight else 0
    if y > 0 and (y + gain > cap or price.get(item, 0) >= cfg['hold_min'].get(item, 0) or day >= 28):
        ops.append('HARVEST')
    return ops


def _p15_plan_day(obs, st):
    """Morning plan: planting choice for empty/harvest-today tiles, item needs, hires."""
    day = int(obs['step']) // 24; farm = obs['farms'][int(obs['player'])]
    prices = {k: int(v) for k, v in obs['market']['prices'].items()}
    tiles = farm['tiles']
    plan = {}
    for y in range(10):
        for x in range(10):
            t = tiles[y][x]
            if t == 'LOCKED':
                continue
            free = t is None or (isinstance(t, dict) and t.get('kind') == 'WEED')
            if isinstance(t, dict) and t.get('kind') == 'PLANT':
                c = _P15_CROP[t['crop']]
                age = day - int(t['planted_day'])
                if not c[4] and age >= c[1]:
                    free = True  # harvested today, replant after
            if free:
                crop = _p15_choose_crop(day, prices, st)
                if crop:
                    plan[(x, y)] = crop
    st['plant_plan'] = plan
    need_seeds = {}
    for c in plan.values():
        need_seeds[c] = need_seeds.get(c, 0) + 1
    st['need_seeds'] = need_seeds
    # workload
    work = 0; feeds = 0; ferts = 0
    for y in range(10):
        for x in range(10):
            t = tiles[y][x]
            if isinstance(t, dict) and t.get('kind') == 'PLANT':
                ops = _p15_plant_ops(t, day, True)
                work += len(ops) + 1; ferts += ops.count('FERTILIZE')
                if (x, y) in plan: work += 2
            elif isinstance(t, dict) and t.get('animal'):
                ops = _p15_animal_ops(t, day, True, prices, _P15_CFG)
                work += len(ops) + 1; feeds += ops.count('FEED')
            elif (x, y) in plan:
                work += 3 + (1 if t is not None else 0)
    st['feeds'] = feeds; st['ferts'] = ferts
    units = _p15_units_needed(obs, st, int(obs['step']) % 24)
    st['hires_wanted'] = max(0, min(_P15_CFG['max_hires'], units - 1))
    st['hires_done'] = 0
    st['zones'] = None
    return plan


def _p15_choose_crop(day, prices, st):
    left = 29 - day
    if left >= 5:
        return 'WHEAT'
    if left >= 4:
        return 'CARROT'
    return None


def _p15_work_tiles(obs, st):
    day = int(obs['step']) // 24; farm = obs['farms'][int(obs['player'])]
    prices = {k: int(v) for k, v in obs['market']['prices'].items()}
    items = []
    for y in range(10):
        for x in range(10):
            t = farm['tiles'][y][x]
            w = 0
            if isinstance(t, dict) and t.get('kind') == 'PLANT':
                w = len(_p15_plant_ops(t, day, True)) + (2 if (x, y) in st['plant_plan'] else 0)
            elif isinstance(t, dict) and t.get('animal'):
                w = len(_p15_animal_ops(t, day, True, prices, _P15_CFG))
            elif (x, y) in st['plant_plan']:
                w = 3 if t is None else 4
            if w:
                items.append(((x, y), w))
    return items


def _p15_route_len(route, start):
    steps = 0; cur = start
    for p, w in route:
        steps += _p15_d(cur, p) + w; cur = p
    return steps


def _p15_zones(obs, st, n_units, starts=None):
    """Cheapest-insertion routing: each unit's route starts at its spawn tile; tiles are inserted
    where they add the least travel, keeping each route within the day's remaining steps."""
    items = _p15_work_tiles(obs, st)
    hour = int(obs['step']) % 24
    avail = 23 - hour - 1
    if starts is None:
        starts = [(4, 4)] + [_P15_ACCESS[i % 4] for i in range(n_units - 1)]
    routes = [[] for _ in range(n_units)]
    lens = [2 for _ in range(n_units)]  # pickups
    work = dict(items)
    # far tiles first (seed the routes), then the rest by cheapest insertion
    order = sorted(items, key=lambda it: -_p15_d(it[0], (4.5, 4.5)))
    for p, w in order:
        best = None
        for u in range(n_units):
            r = routes[u]; st0 = starts[u] if u < len(starts) else (4, 4)
            pts = [st0] + r
            for i in range(len(r) + 1):
                a = pts[i]
                if i < len(r):
                    b = r[i]
                    add = _p15_d(a, p) + _p15_d(p, b) - _p15_d(a, b) + w
                else:
                    add = _p15_d(a, p) + w
                if lens[u] + add > avail:
                    continue
                key = (add, lens[u])
                if best is None or key < best[0]:
                    best = (key, u, i, add)
        if best is None:
            # nobody has room: give it to the least loaded unit at its end
            u = min(range(n_units), key=lambda k: lens[k])
            routes[u].append(p); lens[u] += w + 2
            continue
        _, u, i, add = best
        routes[u].insert(i, p); lens[u] += add
    st['route_lens'] = lens
    return routes


def _p15_units_needed(obs, st, hour):
    items = _p15_work_tiles(obs, st)
    avail = 23 - hour - 1
    total = sum(w for _, w in items)
    lo = max(2, int(total / max(1, avail)))
    for n in range(lo, _P15_CFG['max_hires'] + 2):
        routes = _p15_zones(obs, st, n)
        if max(st['route_lens']) <= avail:
            return n
    return _P15_CFG['max_hires'] + 1


def _p15_act(obs, parent, st):
    step = int(obs['step']); day, hour = divmod(step, 24); player = int(obs['player'])
    farm = obs['farms'][player]; private = obs['private']
    prices = {k: int(v) for k, v in obs['market']['prices'].items()}
    minv = obs['market']['inventory']
    if st.get('day') != day:
        st['day'] = day; _P15_REPORT['days'] += 1
        st['jobs'] = {}; st['claims'] = {}; st['loaded'] = {}
        _p15_plan_day(obs, st)
    tiles = farm['tiles']
    positions = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
    invs = private.get('inventories') or []
    n = len(positions)
    if st.get('zones') is None or len(st['zones']) != n:
        st['zones'] = _p15_zones(obs, st, n)
        st['zone_of'] = {}
        for u, z in enumerate(st['zones']):
            for i, p in enumerate(z):
                st['zone_of'][p] = u
        st['route_idx'] = {u: 0 for u in range(n)}
    shed = {k: int(v) for k, v in (private.get('shed') or {}).items()}
    seeds = {k: int(v) for k, v in (private.get('seeds') or {}).items()}
    cmds = []
    claimed_now = set()
    planting_now = {}
    for u in range(n):
        pos = positions[u]; inv = invs[u] if u < len(invs) else {}
        has_w = int(inv.get('WHEAT', 0)) > 0; has_f = int(inv.get('FERTILIZER', 0)) > 0
        cmd = None
        # morning loading: wheat for this unit's feeds, fertilizer for its fertilizing
        if not st['loaded'].get(u):
            zone = st['zones'][u] if u < len(st['zones']) else []
            need_w = 0; need_f = 0
            for (x, y) in zone:
                t = tiles[y][x]
                if isinstance(t, dict) and t.get('animal'):
                    need_w += _p15_animal_ops(t, day, True, prices, _P15_CFG).count('FEED')
                elif isinstance(t, dict) and t.get('kind') == 'PLANT':
                    need_f += _p15_plant_ops(t, day, True).count('FERTILIZE')
            need_w = max(0, need_w - int(inv.get('WHEAT', 0))); need_f = max(0, need_f - int(inv.get('FERTILIZER', 0)))
            if (need_w and shed.get('WHEAT', 0) > 0) or (need_f and shed.get('FERTILIZER', 0) > 0):
                if pos in _P15_ACCESS:
                    if need_w and shed.get('WHEAT', 0) > 0:
                        q = min(need_w, shed['WHEAT']); cmd = ['PICKUP', 'WHEAT', q]; shed['WHEAT'] -= q
                        if not need_f or shed.get('FERTILIZER', 0) <= 0: st['loaded'][u] = True
                    else:
                        q = min(need_f, shed['FERTILIZER']); cmd = ['PICKUP', 'FERTILIZER', q]; shed['FERTILIZER'] -= q
                        st['loaded'][u] = True
                elif hour <= 12:
                    cmd = _p15_toward(pos, _p15_access(pos))
                else:
                    st['loaded'][u] = True
            else:
                st['loaded'][u] = True
        if cmd is None:
            # pick or continue a tile job
            job = st['jobs'].get(u)
            best = None
            if job is not None:
                x, y = job
                if (x, y) in claimed_now:
                    job = None
            cands = []
            route = st['zones'][u] if u < len(st['zones']) else []
            ri = st['route_idx'].get(u, 0)
            own = None
            while ri < len(route):
                p = route[ri]
                owner = st['claims'].get(p)
                if p not in claimed_now and (owner is None or owner == u or owner >= n):
                    t = tiles[p[1]][p[0]]
                    ops = _p15_tile_ops(t, p, day, has_w, has_f, prices, st, seeds, planting_now)
                    if ops:
                        own = (p, ops); break
                ri += 1
            st['route_idx'][u] = ri
            if own is not None:
                cands.append((1e9, 0, own[0], own[1]))
            for yy in (range(10) if own is None else ()):
                for xx in range(10):
                    p = (xx, yy)
                    if p in claimed_now:
                        continue
                    owner = st['claims'].get(p)
                    if owner is not None and owner != u and owner < n:
                        continue
                    t = tiles[yy][xx]
                    ops = _p15_tile_ops(t, p, day, has_w, has_f, prices, st, seeds, planting_now)
                    if not ops:
                        continue
                    urgent = _p15_urgent(t, day)
                    d = _p15_d(pos, p)
                    inzone = st['zone_of'].get(p) == u
                    score = (urgent * 3 + (2 if inzone else 0) + (3 if p == job else 0)) - d * (1.0 if hour < 18 else 0.5)
                    cands.append((score, -d, p, ops))
            if cands:
                cands.sort(reverse=True)
                score, _, p, ops = cands[0]
                prev = st['jobs'].get(u)
                if prev is not None and prev != p and st['claims'].get(prev) == u:
                    st['claims'].pop(prev, None)
                st['jobs'][u] = p; st['claims'][p] = u; claimed_now.add(p)
                w = _p15_toward(pos, p)
                if w:
                    cmd = w
                else:
                    op = ops[0]
                    if op == 'PLANT':
                        crop = st['plant_plan'].get(p)
                        cmd = ['PLANT', crop]; planting_now[crop] = planting_now.get(crop, 0) + 1
                        _P15_REPORT['planted'] += 1
                    elif op == 'HARVEST' and isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get('animal'):
                        cmd = ['HARVEST']; _P15_REPORT['aharvest'] += 1
                    else:
                        cmd = [op]
                        key = {'FERTILIZE': 'fert', 'WATER': 'water', 'HARVEST': 'harvest', 'FEED': 'feed', 'CARE': 'care', 'COLLECT_FERTILIZER': 'collect', 'DIG': 'dig'}.get(op)
                        if key: _P15_REPORT[key] += 1
            else:
                prev = st['jobs'].pop(u, None)
                if prev is not None and st['claims'].get(prev) == u:
                    st['claims'].pop(prev, None)
                carry = sum(int(v) for k, v in inv.items() if k in _P15_SELLABLE and k not in ('WHEAT', 'FERTILIZER'))
                if carry > 0:
                    a = _p15_access(pos)
                    cmd = _p15_toward(pos, a) or ['DROP']
                else:
                    cmd = ['PASS']; _P15_REPORT['idle'] += 1
        cmds.append(cmd)
    # market
    market = []
    if st['hires_done'] < st['hires_wanted'] and hour <= 2:
        k = min(st['hires_wanted'] - st['hires_done'], 8)
        market += [['HIRE'] for _ in range(k)]
        st['hires_done'] += k; _P15_REPORT['hires'] += k
    if hour == 0 or not st.get('bought'):
        st['bought'] = True
        for crop, q in st['need_seeds'].items():
            q = q - seeds.get(crop, 0)
            if q > 0 and len(market) < 10:
                market.append(['BUY_SEED', crop, q])
        feeds_needed = st.get('feeds', 0) + _P15_CFG['wheat_reserve']
        if shed.get('WHEAT', 0) + sum(int(i.get('WHEAT', 0)) for i in invs) < feeds_needed and len(market) < 10:
            market.append(['BUY_PRODUCT', 'WHEAT', feeds_needed - shed.get('WHEAT', 0)])
        if _P15_CFG['buy_fert'] and shed.get('FERTILIZER', 0) < st.get('ferts', 0) and len(market) < 10:
            market.append(['BUY_PRODUCT', 'FERTILIZER', st['ferts'] - shed.get('FERTILIZER', 0)])
    # sells: projected shed after this step's unit actions
    act = {'farmer': cmds[0], 'hands': cmds[1:], 'market': market}
    proj = dict(projected_shed(act, FarmView(obs)))
    keep = {'WHEAT': st.get('feeds', 0) + _P15_CFG['wheat_reserve'] if hour < 20 else _P15_CFG['wheat_reserve'] + len([1 for r in tiles for t in r if isinstance(t, dict) and t.get('animal')]),
            'FERTILIZER': _P15_CFG['fert_reserve']}
    for item in _P15_SELLABLE:
        if len(market) >= 10:
            break
        q = int(proj.get(item, 0)) - keep.get(item, 0)
        if q <= 0:
            continue
        thr = _P15_CFG['sell_min'].get(item, 0) * (1.0 if day < 27 else 0.3)
        k = 0
        while k < q and _r37_market_price(item, int(minv[item]) + k) >= thr:
            k += 1
        if k > 0:
            market.append(['SELL', item, k]); _P15_REPORT['sold'] += k
    act['market'] = market
    return act


def _p15_urgent(t, day):
    if isinstance(t, dict) and t.get('kind') == 'PLANT':
        return 2 if (int(t.get('consecutive_unwatered', 0)) >= 1 and not t.get('watered_today')) else 0
    if isinstance(t, dict) and t.get('animal'):
        return 2 if (int(t.get('consecutive_unfed', 0)) >= 1 and not t.get('fed_today')) else 0
    return 0


def _p15_tile_ops(t, p, day, has_w, has_f, prices, st, seeds, planting_now):
    if t == 'LOCKED':
        return []
    plan = st['plant_plan'].get(p)
    if t is None:
        if plan and seeds.get(plan, 0) - planting_now.get(plan, 0) > 0:
            return ['PLANT']
        return []
    if not isinstance(t, dict):
        return []
    if t.get('kind') == 'WEED':
        if plan and seeds.get(plan, 0) - planting_now.get(plan, 0) > 0:
            return ['DIG']
        return []
    if t.get('kind') == 'PLANT':
        return _p15_plant_ops(t, day, has_f)
    if t.get('animal'):
        return _p15_animal_ops(t, day, has_w, prices, _P15_CFG)
    return []


_P15_PARENT = agent
def agent(observation, configuration=None):
    action = _P15_PARENT(observation, configuration)
    try:
        step = int(observation['step']); player = int(observation['player'])
        st = _P15_STATE.get(player)
        if st is None or step <= st.get('step', -1):
            st = _P15_STATE[player] = {'step': -1}
            for k in _P15_REPORT: _P15_REPORT[k] = 0
        st['step'] = step
        if step < _P15_CFG['start_day'] * 24 or step >= 696:
            return action
        return _p15_act(observation, action, st)
    except Exception:
        _P15_REPORT['errors'] += 1
        import traceback
        _P15_REPORT['last_error'] = traceback.format_exc()[-600:]
    return action
agent.telemetry = _P15_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
