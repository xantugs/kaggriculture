

# =====================================================================================
# TBLOCK: a fertilized tomato block on SE land that the route leaves idle.
# The route never farms SE.  When V233 has bought SE for its sheep, ~20 SE tiles stay
# empty for the rest of the game; optionally SE is bought for the block in tomato towns.
# Tomatoes (one planting, ages 7..10 produce, +2 each when watered and fertilized) are
# worked by a dedicated crew hired after the native hires of the day.
# =====================================================================================
_TB_CFG = __TBCFG__
_TB_STATE = {}
_TB_REPORT = dict(commits=0, bought_land=0, tiles=0, planted=0, crew_hires=0, crew_shortfalls=0, waters=0, ferts=0,
                  harvests=0, harvested_units=0, placed=0, sold_units=0, lost=0, fert_bought=0, errors=0, last_error='')
_TB_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_TB_TOMATO_SHOPS = ('PIZZA_SHOP', 'FARMERS_MARKET')


def _tb_walk(pos, target):
    x, y = pos; tx, ty = target
    if x != tx: return ['EAST' if x < tx else 'WEST']
    if y != ty: return ['SOUTH' if y < ty else 'NORTH']
    return None


def _tb_home(pos):
    return min(_TB_ACCESS, key=lambda p: (abs(pos[0] - p[0]) + abs(pos[1] - p[1]), _TB_ACCESS.index(p)))


def _tb_native_day(player, day):
    native = _IMPL.chassis.players[player]
    tape = _IMPL.chassis.routes[native['route']]
    return tape[day * 24:min((day + 1) * 24, len(tape))]


def _tb_candidates(obs, player):
    """Empty SE tiles, excluding the shed-access tile and V233's sheep block; compact order near the shed."""
    farm = obs['farms'][player]
    v233 = set()
    st233 = _V233_STATES.get(player) if '_V233_STATES' in globals() else None
    if st233 and st233.get('committed'):
        v233 = {(x, y) for y in (5, 6) for x in range(5, 8)}
    out = []
    for y in range(5, 10):
        for x in range(5, 10):
            if (x, y) in v233 or (x, y) == (5, 5): continue
            t = farm['tiles'][y][x]
            if t is None or t == 'LOCKED' or (isinstance(t, dict) and t.get('kind') == 'WEED'):
                out.append((x, y))
    out.sort(key=lambda p: (abs(p[0] - 5) + abs(p[1] - 5), p[1], p[0]))
    return out


def _tb_decide(obs, player, st):
    farm = obs['farms'][player]
    shops = list(obs['town']['unlocked_shops'])
    nshops = sum(s in _TB_TOMATO_SHOPS for s in shops)
    owned = 'SE' in farm['unlocked_quadrants']
    want = _TB_CFG['n_by_shops'][min(nshops, len(_TB_CFG['n_by_shops']) - 1)]
    if want <= 0: return None
    if int(obs['market']['prices'].get('TOMATO', 0)) < _TB_CFG['min_price']: return None
    if not owned:
        if not _TB_CFG.get('buy_land') or nshops < _TB_CFG['buy_min_shops']: return None
        if set(farm['unlocked_quadrants']) != {'NW', 'NE', 'SW'}: return None
        # the route must not plan its own land purchase later
        for d in range(obs['step'] // 24, 30):
            for a in _tb_native_day(player, d):
                if any(o and o[0] == 'BUY_LAND' for o in a.get('market', [])): return None
    tiles = _tb_candidates(obs, player)[:want]
    if len(tiles) < _TB_CFG['min_tiles']: return None
    return dict(tiles=tiles, buy_land=not owned, nshops=nshops)


def _tb_tile_tasks(obs, st, day):
    """Per-tile task list for today: (tile, op) in priority order."""
    farm = obs['farms'][st['player']]
    tasks = []
    for (x, y) in st['tiles']:
        t = farm['tiles'][y][x]
        if (x, y) in st['lost']: continue
        tomato = isinstance(t, dict) and t.get('crop') == 'TOMATO'
        if not tomato:
            if (x, y) in st['planted']:
                st['lost'].add((x, y)); _TB_REPORT['lost'] += 1; continue
            if day <= st['plant_last']:
                if isinstance(t, dict) and t.get('kind') == 'WEED': tasks.append(((x, y), 'DIG'))
                elif t is None: tasks.append(((x, y), 'PLANT'))
            continue
        st['planted'].add((x, y))
        age = day - int(t['planted_day'])
        units = int(t.get('yield_units', 0) or 0)
        done = int(t.get('max_lifespan_step', -1)) >= 0
        if units >= 3 or (done and units > 0) or (day >= 28 and units > 0):
            tasks.append(((x, y), 'HARVEST'))
        if not done and day < 29:
            if not t.get('watered_today') and (int(t.get('consecutive_unwatered', 0)) >= 1 or 7 <= age <= 10 or not _TB_CFG['skip_water']):
                tasks.append(((x, y), 'WATER'))
            if _TB_CFG['fertilize'] and 7 <= age <= 10 and int(t.get('fertilized_until_day', -1)) < day:
                tasks.append(((x, y), 'FERTILIZE'))
    return tasks


def _tb_crew_size(obs, st, day, hour):
    tasks = _tb_tile_tasks(obs, st, day)
    if not tasks: return 0, 0
    n = len(tasks)
    nf = sum(1 for _, op in tasks if op == 'FERTILIZE')
    steps_avail = max(8, 22 - hour)
    # walking: a compact block next to the shed; ~1.3 moves per task plus a return trip
    need = n * (1 + _TB_CFG['move_per_task']) + 4
    k = max(1, -(-int(need) // steps_avail))
    return min(k, _TB_CFG['max_crew']), nf


def _tb_worker(obs, st, actor, role):
    player = st['player']; farm = obs['farms'][player]; private = obs['private']
    step = int(obs['step']); day = step // 24
    pos = tuple(farm['farmer']) if actor == 0 else tuple(farm['hands'][actor - 1])
    inv = private['inventories'][actor] if actor < len(private['inventories']) else {}
    home = _tb_home(pos); dist_home = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
    tom = int(inv.get('TOMATO', 0))
    # final delivery before the day ends (auto-drop may overflow a full shed)
    if tom and step % 24 >= 23 - dist_home:
        return _tb_walk(pos, home) or ['PLACE', 'TOMATO', tom]
    mine = [p for p in role['tiles']]
    tasks = [(p, op) for p, op in _tb_tile_tasks(obs, st, day) if p in mine]
    need_f = sum(1 for _, op in tasks if op == 'FERTILIZE')
    if need_f and int(inv.get('FERTILIZER', 0)) < 1 and not role.get('fert_tried'):
        if pos in _TB_ACCESS:
            role['fert_tried'] = True
            have = int(private['shed'].get('FERTILIZER', 0))
            if have > 0:
                return ['PICKUP', 'FERTILIZER', min(have, need_f)]
        else:
            return _tb_walk(pos, home)
    seeds = int(private['seeds'].get('TOMATO', 0))
    todo = []
    for p, op in tasks:
        if op == 'FERTILIZE' and int(inv.get('FERTILIZER', 0)) < 1: continue
        if op == 'PLANT' and seeds - st['plant_claims'].get(step, 0) <= 0: continue
        todo.append((p, op))
    if todo:
        # nearest tile; on a tile, harvest before water before fertilize
        rank = {'DIG': 0, 'HARVEST': 1, 'PLANT': 2, 'WATER': 3, 'FERTILIZE': 4}
        p, op = min(todo, key=lambda v: (abs(pos[0] - v[0][0]) + abs(pos[1] - v[0][1]), rank[v[1]], mine.index(v[0])))
        w = _tb_walk(pos, p)
        if w: return w
        if op == 'PLANT': st['plant_claims'][step] = st['plant_claims'].get(step, 0) + 1
        return [op] if op != 'PLANT' else ['PLANT', 'TOMATO']
    if tom:
        return _tb_walk(pos, home) or ['PLACE', 'TOMATO', tom]
    if any(int(v) > 0 for k, v in inv.items() if k != 'FERTILIZER'):
        return _tb_walk(pos, home) or ['DROP']
    return ['PASS']


_TB_PARENT = agent
def agent(observation, configuration=None):
    action = _TB_PARENT(observation, configuration)
    try:
        return _tb_apply(observation, action)
    except Exception as ex:
        _TB_REPORT['errors'] += 1; _TB_REPORT['last_error'] = repr(ex)[:200]
        return action


def _tb_apply(obs, action):
    if not isinstance(action, dict): return action
    step = int(obs['step']); player = int(obs['player']); day, hour = divmod(step, 24)
    st = _TB_STATE.get(player)
    if st is None or step <= st['last']:
        st = _TB_STATE[player] = dict(last=step, player=player, committed=False, tiles=[], planted=set(), lost=set(),
                                      crew={}, pending=None, hired_day=-1, plant_claims={}, plant_last=-1)
        if step > 0:
            for k in _TB_REPORT: _TB_REPORT[k] = 0 if k != 'last_error' else ''
    st['last'] = step
    if step >= 696: return action
    farm = obs['farms'][player]; private = obs['private']
    market = list(action.get('market') or [])
    changed = False
    # --- commitment (buy seeds / land) --------------------------------------------------
    if not st['committed'] and not st.get('declined') and day == _TB_CFG['commit_day'] and hour <= _TB_CFG['commit_hour']:
        dec = _tb_decide(obs, player, st)
        if dec is None:
            st['declined'] = True
        else:
            orders = []
            cost = len(dec['tiles']) * 50 + (4000 if dec['buy_land'] else 0)
            if farm['money'] >= cost + _TB_CFG['reserve'] and len(market) + 2 <= 10 and not any(o and o[0] == 'BUY_LAND' for o in market):
                if dec['buy_land']: orders.append(['BUY_LAND'])
                orders.append(['BUY_SEED', 'TOMATO', len(dec['tiles'])])
                market = market + orders; changed = True
                st.update(committed=True, tiles=dec['tiles'], plant_last=day + _TB_CFG['plant_days'] - 1)
                _TB_REPORT['commits'] += 1; _TB_REPORT['tiles'] = len(dec['tiles']); _TB_REPORT['bought_land'] += int(dec['buy_land'])
    if not st['committed']:
        return action if not changed else dict(action, market=market)
    # --- confirm yesterday's / this morning's hires ----------------------------------------
    if st['pending'] is not None:
        pend = st['pending']; st['pending'] = None
        n = len(farm['hands'])
        if n >= pend['first'] + pend['count'] - 1:
            tiles_left = [p for p in st['tiles'] if p not in st['lost']]
            k = pend['count']
            # split tiles into k contiguous groups (tiles are in compact order)
            groups = [tiles_left[i::k] for i in range(k)] if k > 1 else [tiles_left]
            for i in range(k):
                st['crew'][pend['first'] + i] = dict(tiles=groups[i])
            _TB_REPORT['crew_hires'] += k
        else:
            _TB_REPORT['crew_shortfalls'] += 1
    if st.get('crew_day') != day:
        st['crew_day'] = day; st['crew'] = {}
    # --- hire today's crew after the native hires ------------------------------------------
    if st['hired_day'] != day and day >= st['plant_last'] - _TB_CFG['plant_days'] + 1 and hour <= _TB_CFG['hire_deadline']:
        planned = _tb_native_day(player, day)
        later_native = any(o and o[0] == 'HIRE' for a in planned[hour + 1:] for o in a.get('market', []))
        if not later_native:
            k, nf = _tb_crew_size(obs, st, day, hour)
            if k > 0:
                parent_hires = sum(1 for o in market if o and o[0] == 'HIRE')
                if len(market) + k + 1 <= 10:
                    first = len(farm['hands']) + parent_hires + 1
                    extra = [['HIRE'] for _ in range(k)]
                    if nf:
                        have = int(private['shed'].get('FERTILIZER', 0))
                        # keep the parent from selling the fertilizer the crew needs today
                        for o in market:
                            if o and o[0] == 'SELL' and o[1] == 'FERTILIZER':
                                o[2] = max(0, int(o[2]) - nf)
                        market = [o for o in market if not (o and o[0] == 'SELL' and o[1] == 'FERTILIZER' and int(o[2]) <= 0)]
                        if have < nf:
                            extra.append(['BUY_PRODUCT', 'FERTILIZER', nf - have]); _TB_REPORT['fert_bought'] += nf - have
                    market = market + extra; changed = True
                    st['pending'] = dict(first=first, count=k); st['hired_day'] = day
            else:
                st['hired_day'] = day
    # --- crew commands ----------------------------------------------------------------------
    if st['crew']:
        cmds = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
        nunits = 1 + len(farm['hands'])
        cmds = (cmds + [['PASS']] * nunits)[:nunits]
        for actor, role in st['crew'].items():
            if actor >= nunits: continue
            c = _tb_worker(obs, st, actor, role)
            cmds[actor] = c
            k = {'WATER': 'waters', 'FERTILIZE': 'ferts', 'HARVEST': 'harvests', 'PLACE': 'placed'}.get(c[0])
            if k: _TB_REPORT[k] += 1
        action = dict(action); action['farmer'] = cmds[0]; action['hands'] = cmds[1:]; changed = True
    # --- sell tomatoes from the shed -------------------------------------------------------
    shed_t = int(private['shed'].get('TOMATO', 0))
    placing = 0
    for actor in st['crew']:
        pass
    if shed_t > 0 and len(market) < 10 and not any(o and o[0] == 'SELL' and o[1] == 'TOMATO' for o in market):
        price = int(obs['market']['prices'].get('TOMATO', 0))
        if price >= _TB_CFG['sell_min'] or day >= 28:
            q = shed_t if day >= 28 else min(shed_t, _TB_CFG['sell_lot'])
            market = market + [['SELL', 'TOMATO', q]]; changed = True
            _TB_REPORT['sold_units'] += q
    if changed:
        action = dict(action); action['market'] = market
    return action


agent.telemetry = _TB_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
