

# =====================================================================================
# SX (offhand, 2026-09-23): south-east expansion. Top-10 farms own all four quadrants by day 9-12;
# the chassis never buys SE. Once the route has bought SW and cash allows, SX buys SE and farms its
# 25 tiles with complete crop jobs (tomato 8/plant, fertilized wheat 6, carrots) chosen from town
# demand, run by a small crew hired after the native and R51 hires. Produce is sold by SX itself.
# Engine facts used (1.32.7): one-time crops gain +1 (+2 fertilized) per WATER inside ages
# [(max_day+1)//2, max_day]; tomato produces at the end of ages 7-10 (+2 when watered and fertilized).
# =====================================================================================
_SX_PARENT = agent
_SX_CFG = dict(buy_from=11, buy_to=13, reserve=6000, min_hour=4, kmax=3, jobs_per_hand=15,
               tomato=True, tomato_min_shops=1, tomato_per_shop=6, tomato_max=15, tomato_last=17, tomato_min_price=45,
               carrot=True, carrot_min_price=30, carrot_last=26, wheat=True, wheat_last=25,
               fert_wheat=True, fert_carrot=False, fert_tomato=True, sell=True)
_SX_REPORT = dict(sx_bought=0, sx_hires=0, sx_plants=0, sx_harvests=0, sx_sold=0, sx_fert=0, sx_errors=0, sx_seed_units=0)
_SX_STATES = {}
_SX_TILES = [(x, y) for y in range(5, 10) for x in range(5, 10)]
_SX_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_SX_SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50}
_SX_MAXD = {'WHEAT': 4, 'CARROT': 3}
_SX_ITEMS = ('TOMATO', 'CARROT', 'WHEAT')


def _sx_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _sx_walk(pos, t):
    x, y = pos; tx, ty = t
    if x != tx:
        return ['EAST' if x < tx else 'WEST']
    if y != ty:
        return ['SOUTH' if y < ty else 'NORTH']
    return None


def _sx_home(pos):
    return min(_SX_ACCESS, key=lambda p: abs(pos[0] - p[0]) + abs(pos[1] - p[1]))


def _sx_shops(obs, names):
    return sum(s in names for s in obs['town']['unlocked_shops'])


def _sx_choose(obs, st, day):
    """Crop for an empty SE tile planted today (None = leave empty)."""
    c = _SX_CFG; prices = obs['market']['prices']
    tshops = _sx_shops(obs, ('PIZZA_SHOP', 'FARMERS_MARKET'))
    if (c['tomato'] and day <= c['tomato_last'] and tshops >= c['tomato_min_shops'] and prices['TOMATO'] >= c['tomato_min_price']
            and st['tomatoes'] < min(c['tomato_max'], c['tomato_per_shop'] * tshops)):
        return 'TOMATO'
    cshops = 2 * _sx_shops(obs, ('PET_CAFE',)) + _sx_shops(obs, ('FARMERS_MARKET',))
    if c['carrot'] and day <= c['carrot_last'] and cshops >= 1 and prices['CARROT'] >= c['carrot_min_price']:
        return 'CARROT'
    if c['wheat'] and day <= c['wheat_last']:
        return 'WHEAT'
    return None


def _sx_tile_job(tile, day, inv_fert, crop_plan):
    """Next command for one SE tile today, or None. crop_plan: crop to plant if empty."""
    if tile is None:
        return ['PLANT', crop_plan] if crop_plan else None
    if not isinstance(tile, dict):
        return None
    if tile.get('kind') == 'WEED':
        return ['DIG'] if crop_plan else None
    if tile.get('kind') != 'PLANT':
        return None
    crop = tile['crop']; age = day - tile['planted_day']; y = tile.get('yield_units', 0)
    fert_on = tile.get('fertilized_until_day', -1) >= day
    if crop == 'TOMATO':
        if y >= 4 or (age >= 11 and y > 0) or (day == 29 and y > 0):
            return ['HARVEST']
        if age >= 11:
            return ['DIG'] if crop_plan else None
        if _SX_CFG['fert_tomato'] and age in (7, 10) and not fert_on and inv_fert > 0:
            return ['FERTILIZE']
        if not tile.get('watered_today') and day < 29 and (age >= 6 or age % 2 == 0):
            return ['WATER']
        return None
    if crop in _SX_MAXD:
        md = _SX_MAXD[crop]; w0 = (md + 1) // 2
        want_fert = _SX_CFG['fert_wheat'] if crop == 'WHEAT' else _SX_CFG['fert_carrot']
        if want_fert and w0 <= age <= md - 1 and not fert_on and inv_fert > 0 and not tile.get('watered_today'):
            return ['FERTILIZE']
        if not tile.get('watered_today') and (age == 0 or age >= w0):
            return ['WATER']
        if age >= md and y > 0:
            return ['HARVEST']
        return None
    return None


def _sx_state(player, step):
    st = _SX_STATES.get(player)
    if st is None or step <= st['step']:
        st = _SX_STATES[player] = dict(step=-1, bought=False, day=-1, crew=[], pending=None, plan={}, tomatoes=0,
                                        requested_day=-1, own={'TOMATO': 0, 'CARROT': 0, 'WHEAT': 0}, last_inv={}, last_cmd={})
        for k in _SX_REPORT:
            _SX_REPORT[k] = 0
    st['step'] = step
    return st


def _sx_act(obs, action, st):
    step = int(obs['step']); day = step // 24; hour = step % 24; player = int(obs['player'])
    farm = obs['farms'][player]; private = obs['private']; c = _SX_CFG
    market = list(action.get('market') or [])
    quads = set(farm['unlocked_quadrants'])
    # 1. land
    # The yarn-town sheep project (V233) buys SE in its day-11 (hour<=3) / day-12 (hour<=1) windows; SX
    # waits for those and never uses land it did not buy itself.
    if (_V233_STATES.get(player) or {}).get('committed'):
        return action
    if not st['bought']:
        if 'SE' in quads:
            if st.get('buy_step') is None:
                return action
            st['bought'] = True
        elif (c['buy_from'] <= day <= c['buy_to'] and quads == {'NW', 'NE', 'SW'} and (day > 11 or hour >= 4)
              and (day != 12 or hour >= 2) and not any(o and o[0] == 'BUY_LAND' for o in market)
              and farm['money'] >= 4000 + c['reserve'] and len(market) < 10 and st.get('buy_step') is None):
            market.append(['BUY_LAND']); _SX_REPORT['sx_bought'] += 1; st['buy_step'] = step
            out = dict(action); out['market'] = market
            return out
    if not st['bought']:
        return action
    if st['day'] != day:
        for inv in st['last_inv'].values():          # end-of-day auto-drop into the shed
            for it, q in inv.items():
                st['own'][it] += q
        st['last_inv'] = {}; st['last_cmd'] = {}
        st['day'] = day; st['crew'] = []; st['requested_day'] = -1
    else:
        for actor, prev in st['last_inv'].items():
            if st['last_cmd'].get(actor, [''])[0] in ('DROP', 'PLACE') and actor < len(private['inventories']):
                cur = private['inventories'][actor]
                for it, q in prev.items():
                    st['own'][it] += max(0, q - int(cur.get(it, 0)))
    tiles = farm['tiles']
    st['tomatoes'] = sum(1 for (x, y) in _SX_TILES if isinstance(tiles[y][x], dict) and tiles[y][x].get('crop') == 'TOMATO'
                         and day - tiles[y][x]['planted_day'] < 11)
    # 2. confirm crew hired last step
    if st['pending']:
        first, k = st['pending']; st['pending'] = None
        n = len(farm['hands'])
        st['crew'] = [i for i in range(first, first + k) if i <= n]
        _SX_REPORT['sx_hires'] += len(st['crew'])
    # 3. today's plan: crops for empty/weeded tiles, workload, crew request
    if st['requested_day'] != day and hour >= c['min_hour'] and day <= 29:
        native = _IMPL.chassis.players[player]
        tape = _IMPL.chassis.routes[2 if step >= 648 else native['route']]
        later_hire = any(o and o[0] == 'HIRE' for t in range(step + 1, min((day + 1) * 24, len(tape))) for o in tape[t].get('market', []))
        if not later_hire and not any(o and o[0] == 'HIRE' for o in market):
            st['requested_day'] = day
            plan = {}; seeds = collections.Counter()
            for (x, y) in _SX_TILES:
                t = tiles[y][x]
                if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED') or (
                        isinstance(t, dict) and t.get('crop') == 'TOMATO' and day - t['planted_day'] >= 11):
                    cr = _sx_choose(obs, st, day)
                    if cr:
                        plan[(x, y)] = cr; seeds[cr] += 1
                        if cr == 'TOMATO':
                            st['tomatoes'] += 1
            st['plan'] = plan
            jobs = 0
            for (x, y) in _SX_TILES:
                t = tiles[y][x]
                if (x, y) in plan:
                    jobs += 2 + (isinstance(t, dict))
                elif isinstance(t, dict) and t.get('kind') == 'PLANT':
                    age = day - t['planted_day']
                    jobs += 1 + (t['crop'] == 'TOMATO' and age in (7, 9, 10, 11)) + (t['crop'] in _SX_MAXD and age >= 2)
            k = min(c['kmax'], -(-jobs // c['jobs_per_hand'])) if jobs else 0
            need_fert = sum(1 for (x, y) in _SX_TILES if isinstance(tiles[y][x], dict) and tiles[y][x].get('kind') == 'PLANT' and (
                (tiles[y][x]['crop'] == 'TOMATO' and day - tiles[y][x]['planted_day'] in (7, 10)) or
                (tiles[y][x]['crop'] == 'WHEAT' and c['fert_wheat'] and 1 <= day - tiles[y][x]['planted_day'] <= 2)))
            orders = []
            for cr, n in seeds.items():
                have = int(private['seeds'].get(cr, 0))
                if n > have:
                    orders.append(['BUY_SEED', cr, n - have]); _SX_REPORT['sx_seed_units'] += n - have
            if need_fert and private['shed'].get('FERTILIZER', 0) < need_fert:
                orders.append(['BUY_PRODUCT', 'FERTILIZER', need_fert - int(private['shed'].get('FERTILIZER', 0))])
            cost = sum(_sx_fib(farm['hires_today'] + i) for i in range(k)) + sum(o[2] * _SX_SEED.get(o[1], 0) for o in orders if o[0] == 'BUY_SEED')
            if k and farm['money'] >= cost + 1500 and len(market) + len(orders) + k <= 10:
                market += orders + [['HIRE'] for _ in range(k)]
                st['pending'] = (len(farm['hands']) + 1, k)
    # 4. crew commands
    cmds = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
    n_units = 1 + len(farm['hands'])
    cmds += [['PASS'] for _ in range(n_units - len(cmds))]
    if st['crew']:
        invs = private['inventories']
        planting = collections.Counter(cm[1] for cm in cmds if isinstance(cm, list) and len(cm) > 1 and cm[0] == 'PLANT')
        seeds_left = {cr: int(private['seeds'].get(cr, 0)) - planting.get(cr, 0) for cr in _SX_SEED}
        claimed = set()
        shed_fert = int(private['shed'].get('FERTILIZER', 0))
        k = len(st['crew'])
        for j, actor in enumerate(st['crew']):
            if actor >= n_units:
                continue
            pos = tuple(farm['hands'][actor - 1]); inv = invs[actor] if actor < len(invs) else {}
            mine = [xy for i, xy in enumerate(_SX_TILES) if (xy[0] - 5) * k // 5 == j] if k > 1 else _SX_TILES
            cmd = None
            carried = sum(int(inv.get(it, 0)) for it in _SX_ITEMS)
            home = _sx_home(pos); dist = abs(pos[0] - home[0]) + abs(pos[1] - home[1])
            if (day == 29 and step >= 717 - dist and carried) or carried >= 20:
                cmd = _sx_walk(pos, home) or ['DROP']
            if cmd is None and pos in _SX_ACCESS and inv.get('FERTILIZER', 0) == 0 and shed_fert > 0 and hour <= 20:
                want = sum(1 for (x, y) in mine if isinstance(tiles[y][x], dict) and tiles[y][x].get('kind') == 'PLANT' and (
                    (tiles[y][x]['crop'] == 'TOMATO' and day - tiles[y][x]['planted_day'] in (7, 10)) or
                    (tiles[y][x]['crop'] == 'WHEAT' and c['fert_wheat'] and 2 <= day - tiles[y][x]['planted_day'] <= 3) or
                    (tiles[y][x]['crop'] == 'CARROT' and c['fert_carrot'] and day - tiles[y][x]['planted_day'] == 2)))
                if want:
                    q = min(want, shed_fert); shed_fert -= q
                    cmd = ['PICKUP', 'FERTILIZER', q]
            if cmd is None:
                best = None
                for xy in mine:
                    if xy in claimed:
                        continue
                    x, y = xy; t = tiles[y][x]
                    job = _sx_tile_job(t, day, int(inv.get('FERTILIZER', 0)), st['plan'].get(xy))
                    if job is None:
                        continue
                    if job[0] == 'PLANT' and seeds_left.get(job[1], 0) <= 0:
                        continue
                    d = abs(pos[0] - x) + abs(pos[1] - y)
                    if best is None or d < best[0]:
                        best = (d, xy, job)
                if best:
                    d, xy, job = best; claimed.add(xy)
                    cmd = _sx_walk(pos, xy) or job
                    if cmd[0] == 'PLANT':
                        seeds_left[cmd[1]] -= 1; _SX_REPORT['sx_plants'] += 1
                        if st['plan'].get(xy) == cmd[1]:
                            st['plan'].pop(xy, None)
                    elif cmd[0] == 'HARVEST':
                        _SX_REPORT['sx_harvests'] += 1
                    elif cmd[0] == 'FERTILIZE':
                        _SX_REPORT['sx_fert'] += 1
            if cmd is None:
                cmd = (_sx_walk(pos, home) or ['DROP']) if carried else ['PASS']
            cmds[actor] = cmd
            st['last_cmd'][actor] = cmd
            st['last_inv'][actor] = {it: int(inv.get(it, 0)) for it in _SX_ITEMS if inv.get(it, 0)}
    # 5. sell SX produce from the shed
    if c['sell'] and len(market) < 10:
        for it in _SX_ITEMS:
            q = min(st['own'][it], int(private['shed'].get(it, 0)))
            if q > 0 and len(market) < 10 and not any(o[:2] == ['SELL', it] for o in market):
                market.append(['SELL', it, q]); st['own'][it] -= q; _SX_REPORT['sx_sold'] += q
    out = dict(action); out['farmer'] = cmds[0]; out['hands'] = cmds[1:]; out['market'] = market
    return out


def agent(observation, configuration=None):
    action = _SX_PARENT(observation, configuration)
    try:
        st = _sx_state(int(observation['player']), int(observation['step']))
        if isinstance(action, dict) and int(observation['step']) >= 24 * _SX_CFG['buy_from']:
            action = _sx_act(observation, action, st)
    except Exception as e:
        _SX_REPORT['sx_errors'] += 1; _SX_REPORT['sx_last_error'] = repr(e)[:160]
    return action


agent.telemetry = _SX_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
