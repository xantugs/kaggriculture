

# =====================================================================================
# CSUB: carrot substitution.  The route's 3-day wheat cycle (plant, water at ages 0/2/3,
# harvest at age 3) is exactly a carrot's cycle, so on tiles whose next route harvest comes at
# age 3 a wheat planting can become a carrot with no change to the route's labor.  Done only
# while carrots are worth clearly more than wheat.
# =====================================================================================
_KSUB_CFG = __CSCFG__
_KSUB_STATE = {}
_KSUB_REPORT = dict(subs=0, seeds=0, skipped_age=0, skipped_price=0, errors=0, last_error='')
_KSUB_MOVES = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
_KSUB_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))


def _ksub_tape_ops(player, d0, d1):
    """Native tape from day d0 to d1-1: {tile: [(step, op), ...]} for non-move commands."""
    native = _IMPL.chassis.players[player]
    out = {}
    for day in range(d0, d1):
        route = 2 if day * 24 >= 648 else native['route']
        tape = _IMPL.chassis.routes[route]
        pos = [(4, 4)]
        for t in range(day * 24, min((day + 1) * 24, len(tape))):
            a = tape[t] or {}
            cmds = [a.get('farmer') or ['PASS']] + list(a.get('hands') or [])
            for u in range(len(pos)):
                c = cmds[u] if u < len(cmds) else ['PASS']
                if not c: continue
                if c[0] in _KSUB_MOVES:
                    dx, dy = _KSUB_MOVES[c[0]]; x, y = pos[u]; nx, ny = x + dx, y + dy
                    if 0 <= nx < 10 and 0 <= ny < 10: pos[u] = (nx, ny)
                elif c[0] != 'PASS':
                    out.setdefault(pos[u], []).append((t, c[0]))
            for o in a.get('market') or []:
                if o and o[0] == 'HIRE':
                    occ = {q: 0 for q in _KSUB_ACCESS}
                    for p in pos:
                        if p in occ: occ[p] += 1
                    pos.append(sorted(occ.items(), key=lambda kv: (kv[1], _KSUB_ACCESS.index(kv[0])))[0][0])
    return out


def _ksub_worth(obs):
    pr = obs['market']['prices']
    shops = obs['town']['unlocked_shops']
    cshops = sum(2 if s == 'PET_CAFE' else 1 for s in shops if s in ('PET_CAFE', 'FARMERS_MARKET'))
    if cshops < _KSUB_CFG['min_carrot_shops']: return False
    return int(pr.get('CARROT', 0)) >= _KSUB_CFG['ratio'] * int(pr.get('WHEAT', 0)) + _KSUB_CFG['margin']


_KSUB_PARENT = agent
def agent(observation, configuration=None):
    action = _KSUB_PARENT(observation, configuration)
    try:
        return _ksub_apply(observation, action)
    except Exception as ex:
        _KSUB_REPORT['errors'] += 1; _KSUB_REPORT['last_error'] = repr(ex)[:200]
        return action


def _ksub_apply(obs, action):
    if not isinstance(action, dict): return action
    step = int(obs['step']); player = int(obs['player']); day, hour = divmod(step, 24)
    st = _KSUB_STATE.get(player)
    if st is None or step <= st['last']:
        st = _KSUB_STATE[player] = dict(last=step, day=-1, look={}, today=0)
        if step > 0:
            for k in _KSUB_REPORT: _KSUB_REPORT[k] = 0 if k != 'last_error' else ''
    st['last'] = step
    if day < _KSUB_CFG['from_day'] or day > _KSUB_CFG['to_day']: return action
    if st['day'] != day:
        st['day'] = day; st['today'] = 0
        st['look'] = _ksub_tape_ops(player, day, min(30, day + 5))
    farm = obs['farms'][player]; private = obs['private']
    market = list(action.get('market') or [])
    changed = False
    # buy carrot seeds one step ahead: count the wheat plantings the tape makes next step on eligible tiles
    cmds = [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])
    pos = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
    worth = _ksub_worth(obs)
    subs = []
    for i, c in enumerate(cmds):
        if i >= len(pos) or not c or c[0] != 'PLANT' or len(c) < 2 or c[1] != 'WHEAT': continue
        x, y = pos[i]
        if farm['tiles'][y][x] is not None: continue
        if not worth:
            _KSUB_REPORT['skipped_price'] += 1; continue
        if st['today'] + len(subs) >= _KSUB_CFG['max_per_day']: continue
        ops = [(t, op) for t, op in st['look'].get((x, y), []) if t > step]
        nh = next((t for t, op in ops if op == 'HARVEST'), None)
        if nh is None or nh // 24 - day != 3 or not any(op == 'WATER' and t // 24 == day for t, op in ops) :
            # the planting-day watering must follow on the same day, and the next harvest must be at age 3
            if nh is None or nh // 24 - day != 3:
                _KSUB_REPORT['skipped_age'] += 1; continue
        subs.append(i)
    if subs:
        have = int(private['seeds'].get('CARROT', 0))
        n_carrot_cmds = sum(1 for c in cmds if c and c[0] == 'PLANT' and len(c) > 1 and c[1] == 'CARROT')
        k = min(len(subs), max(0, have - n_carrot_cmds))
        if k > 0:
            cmds = [list(c) if c else ['PASS'] for c in cmds]
            for i in subs[:k]:
                cmds[i] = ['PLANT', 'CARROT']
            st['today'] += k; _KSUB_REPORT['subs'] += k
            action = dict(action); action['farmer'] = cmds[0]; action['hands'] = cmds[1:]; changed = True
    # keep a carrot seed stock for the next steps' substitutions
    if worth and st['today'] < _KSUB_CFG['max_per_day'] and len(market) < 10:
        want = _KSUB_CFG['seed_stock']
        have = int(private['seeds'].get('CARROT', 0))
        if have < want and not any(o and o[0] == 'BUY_SEED' and o[1] == 'CARROT' for o in market):
            market = market + [['BUY_SEED', 'CARROT', want - have]]; changed = True
            _KSUB_REPORT['seeds'] += want - have
            action = dict(action); action['market'] = market
    return action


agent.telemetry = _KSUB_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
