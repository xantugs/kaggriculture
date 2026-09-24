

# =====================================================================================
# SE tomato annex. None of the 41 route tapes ever buys the SE quadrant (they buy NE on
# day 6 and SW on day 11). In towns with tomato demand (pizza shops / farmers markets) we
# buy SE after the route's SW purchase and grow a dedicated tomato block with our own
# daily crew: water on survival/production days, fertilize twice (the fertilized
# refreshes give 2 units each), harvest before the 4-unit cap, deliver and sell.
# The route's land, workers and hires are untouched: our crew is hired after all native
# and chassis hires of the day and only ever commands its own hand indices.
# =====================================================================================
_AX_CFG = __AXCFG__
_AX_STATES = {}
_AX_REPORT = dict(commit=0, declined=0, hires=0, hire_cost=0, planted=0, harvested=0, sold=0, revenue_req=0,
                  fert_bought=0, fert_applied=0, waters=0, lost=0, errors=0, shortfalls=0)
_AX_TSHOPS = ('PIZZA_SHOP', 'FARMERS_MARKET')
_AX_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))


def _ax_tiles(n):
    # serpentine-friendly order: nearest rows first, alternating direction
    rows = []
    for y in _AX_CFG['rows']:
        r = [(x, y) for x in range(5, 10)]
        if (y - 5) % 2: r.reverse()
        rows.extend(r)
    return rows[:n]


def _ax_walk(pos, target):
    x, y = pos; tx, ty = target
    if x != tx: return ['EAST' if x < tx else 'WEST']
    if y != ty: return ['SOUTH' if y < ty else 'NORTH']
    return None


def _ax_due(tile, day):
    """Actions due today on one tomato plot, in the order to perform them."""
    out = []
    if not (isinstance(tile, dict) and tile.get('crop') == 'TOMATO'):
        return out
    age = day - int(tile.get('planted_day', day))
    fert_days = _AX_CFG['fert_ages']
    if age in fert_days and int(tile.get('fertilized_until_day', -1)) < day + 2 - 0:
        # a single application covers day..day+2
        if int(tile.get('fertilized_until_day', -1)) < day:
            out.append('FERTILIZE')
    if not tile.get('watered_today') and day < 29 and (int(tile.get('consecutive_unwatered', 0)) >= 1 or 7 <= age <= 10 or age in _AX_CFG['extra_water']):
        out.append('WATER')
    y = int(tile.get('yield_units', 0))
    if y > 0 and (y >= 3 or age >= 11 or day >= 28):
        out.append('HARVEST')
    return out


def _ax_plot_work(tile, day, state, private):
    if tile is None:
        return state.get('to_plant', 0) > 0
    if isinstance(tile, dict) and tile.get('kind') == 'WEED':
        return state.get('to_plant', 0) > 0
    return bool(_ax_due(tile, day))


def _ax_market_room(action):
    return 10 - len(action.get('market') or [])


def _ax_budget(obs, action, extra_hires, extra_cost):
    farm = obs['farms'][int(obs['player'])]
    hires = int(farm['hires_today']) + sum(1 for o in action.get('market', []) if o and o[0] == 'HIRE')
    cost = extra_cost + sum(_v219_fib(n) for n in range(hires, hires + extra_hires))
    for o in action.get('market', []):
        if not o: continue
        if o[0] == 'BUY_PRODUCT' and len(o) > 2: cost += int(o[2]) * (int(obs['market']['prices'][o[1]]) + 10)
        elif o[0] == 'BUY_ANIMAL' and len(o) > 2: cost += int(o[2]) * {'COW': 400, 'SHEEP': 500, 'GOOSE': 300}.get(o[1], 500)
        elif o[0] == 'BUY_SEED' and len(o) > 2: cost += int(o[2]) * {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}.get(o[1], 100)
        elif o[0] == 'BUY_LAND': cost += 4000
        elif o[0] == 'HIRE': pass
    return cost


def _ax_can_hire_now(obs, action, state, player):
    step = int(obs['step']); day, hour = divmod(step, 24)
    native = _IMPL.chassis.players.get(player)
    if native is None: return False
    planned = _v219_native_day(native, day)
    if any(o and o[0] == 'HIRE' for a in planned[hour + 1:] for o in a.get('market', [])): return False
    if native.get('pending'): return False
    if any(o and o[0] == 'HIRE' for o in action.get('market', [])): return False
    if _R51_INPUT_STATES.get(player, {}).get('pending'): return False
    for parent in (_V219_STATES.get(player, {}), _V233_STATES.get(player, {})):
        if parent.get('pending'): return False
    # leave the chassis's own input-worker window (days 12-28, hours 1-3) alone
    if 12 <= day <= 28 and hour < _AX_CFG['hire_hour']: return False
    if hour < 2: return False
    return True


def _ax_plan_crew(obs, state, day, hour):
    farm = obs['farms'][int(obs['player'])]
    visits = 0; acts = 0; fert = 0
    planted_cap = min(_AX_CFG['batch'], state.get('to_plant', 0))
    for (x, y) in state['plots']:
        t = farm['tiles'][y][x]
        if t is None or (isinstance(t, dict) and t.get('kind') == 'WEED'):
            if state.get('to_plant', 0) > 0 and planted_cap > 0:
                planted_cap -= 1; visits += 1; acts += 2 + (1 if t is not None else 0)
            continue
        due = _ax_due(t, day)
        if due:
            visits += 1; acts += len(due); fert += due.count('FERTILIZE')
    if not visits: return 0, 0
    avail = 23 - hour - 1
    for crew in range(1, _AX_CFG['max_crew'] + 1):
        per_worker = (acts + visits * _AX_CFG['move_per_visit']) / crew + _AX_CFG['overhead'] + (1 if fert else 0)
        if per_worker <= avail: return crew, fert
    return _AX_CFG['max_crew'], fert


def _ax_commit_ok(obs, action, state, player):
    step = int(obs['step']); day, hour = divmod(step, 24)
    farm = obs['farms'][player]
    if not (_AX_CFG['d0'] <= day <= _AX_CFG['d1']): return False
    if len(farm['tiles']) != 10 or set(farm['unlocked_quadrants']) != {'NW', 'NE', 'SW'}: return False
    if _V233_STATES.get(player, {}).get('committed') or _V219_STATES.get(player, {}).get('committed'): return False
    k = sum(s in _AX_TSHOPS for s in obs['town']['unlocked_shops'])
    if k < _AX_CFG['k']: return False
    if int(obs['market']['prices']['TOMATO']) < _AX_CFG['min_price']: return False
    return True


def _ax_control(obs, action, state):
    player = int(obs['player']); step = int(obs['step']); day, hour = divmod(step, 24)
    farm = obs['farms'][player]; private = obs['private']
    if day >= 29: return action
    if state.get('day') != day:
        state['day'] = day; state['workers'] = {}; state['hired_today'] = False; state['pending'] = None; state['planted_today'] = 0
    # confirm yesterday's/this morning's pending hire
    if state.get('pend'):
        p = state.pop('pend')
        if len(farm['hands']) >= p['first'] + p['count'] - 1:
            for i in range(p['count']):
                state['workers'][p['first'] + i] = dict(index=i, count=p['count'], fert=p['fert'], loaded=False)
        else:
            _AX_REPORT['shortfalls'] += 1
    # commit
    if not state.get('committed'):
        if state.get('declined') or not _ax_commit_ok(obs, action, state, player): return action
        if not _ax_can_hire_now(obs, action, state, player): return action
        n = _AX_CFG['n']
        k = sum(s in _AX_TSHOPS for s in obs['town']['unlocked_shops'])
        if k >= 3: n = _AX_CFG['n3']
        state['plots'] = _ax_tiles(n); state['plant_day'] = day; state['to_plant'] = n
        crew = min(_AX_CFG['max_crew'], max(1, -(-(3 * min(n, _AX_CFG['batch']) + 4) // max(6, 23 - hour - 2))))
        extra = [['BUY_LAND'], ['BUY_SEED', 'TOMATO', n]] + [['HIRE'] for _ in range(crew)]
        if _ax_market_room(action) < len(extra): return action
        cost = _ax_budget(obs, action, crew, 4000 + 50 * n)
        if farm['money'] < cost + _AX_CFG['reserve']:
            return action
        state['committed'] = True; _AX_REPORT['commit'] += 1
        h0 = int(farm['hires_today']) + sum(1 for o in action.get('market', []) if o and o[0] == 'HIRE')
        _AX_REPORT['hire_cost'] += sum(_v219_fib(h) for h in range(h0, h0 + crew))
        state['pend'] = dict(first=len(farm['hands']) + 1, count=crew, fert=0)
        state['hired_today'] = True; _AX_REPORT['hires'] += crew
        out = copy.deepcopy(action); out['market'] = list(out.get('market') or []) + extra
        return out
    out = action
    # daily crew
    if not state.get('hired_today') and 'SE' in farm['unlocked_quadrants'] and _ax_can_hire_now(obs, action, state, player):
        crew, fert = _ax_plan_crew(obs, state, day, hour)
        if crew:
            extra = []
            fert_q = 0
            if fert:
                fert_q = fert + 1
                if fert_q: extra.append(['BUY_PRODUCT', 'FERTILIZER', fert_q])
            extra += [['HIRE'] for _ in range(crew)]
            if _ax_market_room(action) >= len(extra):
                cost = _ax_budget(obs, action, crew, fert_q * (int(obs['market']['prices']['FERTILIZER']) + 5))
                if farm['money'] >= cost + 1000:
                    state['pend'] = dict(first=len(farm['hands']) + 1, count=crew, fert=fert)
                    h0 = int(farm['hires_today']) + sum(1 for o in action.get('market', []) if o and o[0] == 'HIRE')
                    _AX_REPORT['hire_cost'] += sum(_v219_fib(h) for h in range(h0, h0 + crew))
                    state['hired_today'] = True; _AX_REPORT['hires'] += crew; _AX_REPORT['fert_bought'] += fert_q
                    out = copy.deepcopy(action); out['market'] = list(out.get('market') or []) + extra
        else:
            state['hired_today'] = True
    # worker control
    if state['workers']:
        view = FarmView(obs)
        cmds = [out.get('farmer') or ['PASS']] + [list(c) for c in (out.get('hands') or [])]
        cmds += [['PASS'] for _ in range(len(farm['hands']) + 1 - len(cmds))]
        plots = state['plots']
        # (re)assign contiguous plot segments once per day, after confirmation
        if not state.get('segments_day') == day:
            state['segments_day'] = day
            actors = sorted(state['workers'])
            work = [p for p in plots if _ax_plot_work(farm['tiles'][p[1]][p[0]], day, state, private)]
            n = max(1, len(actors))
            per = -(-len(work) // n) if work else 0
            for i, a in enumerate(actors):
                state['workers'][a]['seg'] = work[i * per:(i + 1) * per]
        claimed = set()
        for actor in sorted(state['workers']):
            if actor >= len(cmds) or actor > len(farm['hands']): continue
            role = state['workers'][actor]
            pos = tuple(farm['hands'][actor - 1]); inv = view.inventory(actor)
            cmd = None
            home = min(_AX_ACCESS, key=lambda p: abs(p[0] - pos[0]) + abs(p[1] - pos[1]))
            dist = abs(home[0] - pos[0]) + abs(home[1] - pos[1])
            seg = role.get('seg') or []
            need_f = sum(1 for p in seg if 'FERTILIZE' in _ax_due(farm['tiles'][p[1]][p[0]], day))
            if need_f and inv.get('FERTILIZER', 0) < need_f and not role.get('loaded'):
                if pos in _AX_ACCESS:
                    stock = int(private['shed'].get('FERTILIZER', 0))
                    if stock > 0:
                        cmd = ['PICKUP', 'FERTILIZER', min(stock, need_f - inv.get('FERTILIZER', 0))]
                    role['tries'] = role.get('tries', 0) + 1
                    if role['tries'] >= 2 or stock >= need_f - inv.get('FERTILIZER', 0): role['loaded'] = True
                else:
                    cmd = _ax_walk(pos, home)
            if cmd is None:
                def tasks_at(p):
                    x, y = p; t = farm['tiles'][y][x]
                    if t is None:
                        if state.get('to_plant', 0) > 0 and int(private['seeds'].get('TOMATO', 0)) > 0 and state.get('planted_today', 0) < _AX_CFG['batch']:
                            return ['PLANT', 'TOMATO']
                        return None
                    if isinstance(t, dict) and t.get('kind') == 'WEED':
                        if state.get('to_plant', 0) > 0 and int(private['seeds'].get('TOMATO', 0)) > 0:
                            return ['DIG']
                        return None
                    due = _ax_due(t, day)
                    if due and due[0] == 'FERTILIZE' and inv.get('FERTILIZER', 0) <= 0: due = due[1:]
                    return [due[0]] if due else None
                own = [(p, tasks_at(p)) for p in seg if p not in claimed]
                own = [(p, c) for p, c in own if c]
                if not own:
                    others = [(p, tasks_at(p)) for p in plots if p not in claimed]
                    own = [(p, c) for p, c in others if c]
                carry = int(inv.get('TOMATO', 0))
                if carry and (hour >= 22 - dist or carry >= _AX_CFG['deliver_at'] or not own):
                    cmd = _ax_walk(pos, home) or ['PLACE', 'TOMATO', carry]
                elif own:
                    # serpentine order inside the segment, nearest first across segments
                    tgt, c = min(own, key=lambda v: (abs(v[0][0] - pos[0]) + abs(v[0][1] - pos[1]), plots.index(v[0])))
                    claimed.add(tgt)
                    w = _ax_walk(pos, tgt)
                    cmd = w or c
                    if not w:
                        if c[0] == 'PLANT': state['to_plant'] -= 1; state['planted_today'] = state.get('planted_today', 0) + 1; _AX_REPORT['planted'] += 1
                        elif c[0] == 'HARVEST': _AX_REPORT['harvested'] += int(farm['tiles'][tgt[1]][tgt[0]].get('yield_units', 0))
                        elif c[0] == 'FERTILIZE': _AX_REPORT['fert_applied'] += 1
                        elif c[0] == 'WATER': _AX_REPORT['waters'] += 1
                else:
                    cmd = ['PASS']
            cmds[actor] = cmd
        out = copy.deepcopy(out) if out is action else out
        out['farmer'], out['hands'] = cmds[0], cmds[1:]
    # sell tomatoes (our shed stock after this step's unit actions)
    if state.get('committed') and not any(o and o[:2] == ['SELL', 'TOMATO'] for o in out.get('market', [])) and _ax_market_room(out) > 0:
        q = int(projected_shed(out, FarmView(obs)).get('TOMATO', 0))
        if q > 0 and int(obs['market']['prices']['TOMATO']) >= _AX_CFG['sell_floor']:
            out = copy.deepcopy(out) if out is action else out
            out['market'] = list(out.get('market') or []) + [['SELL', 'TOMATO', q]]
            _AX_REPORT['sold'] += q
    return out


_AX_PARENT = agent
def agent(observation, configuration=None):
    action = _AX_PARENT(observation, configuration)
    try:
        player = int(observation['player']); step = int(observation['step'])
        state = _AX_STATES.get(player)
        if state is None or step <= state.get('step', -1):
            state = _AX_STATES[player] = {'step': -1}
            for k in _AX_REPORT: _AX_REPORT[k] = 0
        state['step'] = step
        if isinstance(action, dict):
            return _ax_control(observation, action, state)
    except Exception:
        _AX_REPORT['errors'] += 1
    return action
agent.telemetry = _AX_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
