

# =====================================================================================
# TTOWN: tomato towns.  With 3+ tomato buyers the tomato price runs far above wheat, so on
# day _KTT_CFG['day'] some of the route's wheat plantings become tomatoes.  The route keeps
# visiting those plots on its wheat rhythm (never two dry days in a row), its age-9 harvest
# collects the first tomatoes and the final-day controller the rest.  No extra workers.
# =====================================================================================
_KTT_CFG = __TTCFG__
_KTT_STATE = {}
_KTT_REPORT = dict(armed=0, subs=0, seeds=0, blocked_dig=0, sold=0, skipped_dry=0, errors=0, last_error='')
_KTT_MOVES = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
_KTT_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))


def _ktt_tape_ops(player, d0, d1):
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
                if c[0] in _KTT_MOVES:
                    dx, dy = _KTT_MOVES[c[0]]; x, y = pos[u]; nx, ny = x + dx, y + dy
                    if 0 <= nx < 10 and 0 <= ny < 10: pos[u] = (nx, ny)
                elif c[0] != 'PASS':
                    out.setdefault(pos[u], []).append((t, c[0]))
            for o in a.get('market') or []:
                if o and o[0] == 'HIRE':
                    occ = {q: 0 for q in _KTT_ACCESS}
                    for p in pos:
                        if p in occ: occ[p] += 1
                    pos.append(sorted(occ.items(), key=lambda kv: (kv[1], _KTT_ACCESS.index(kv[0])))[0][0])
    return out


_KTT_PARENT = agent
def agent(observation, configuration=None):
    action = _KTT_PARENT(observation, configuration)
    try:
        return _ktt_apply(observation, action)
    except Exception as ex:
        _KTT_REPORT['errors'] += 1; _KTT_REPORT['last_error'] = repr(ex)[:200]
        return action


def _ktt_apply(obs, action):
    if not isinstance(action, dict): return action
    step = int(obs['step']); player = int(obs['player']); day, hour = divmod(step, 24)
    st = _KTT_STATE.get(player)
    if st is None or step <= st['last']:
        st = _KTT_STATE[player] = dict(last=step, armed=False, decided=False, tiles=set(), look={}, want=0)
        if step > 0:
            for k in _KTT_REPORT: _KTT_REPORT[k] = 0 if k != 'last_error' else ''
    st['last'] = step
    if step >= 696: return action
    cfg = _KTT_CFG
    farm = obs['farms'][player]; private = obs['private']
    market = list(action.get('market') or [])
    changed = False
    # decision at the configured step (after V219's own step-432 decision)
    if not st['decided'] and step >= cfg['day'] * 24 + cfg['hour']:
        st['decided'] = True
        shops = obs['town']['unlocked_shops']
        n = sum(s in ('PIZZA_SHOP', 'FARMERS_MARKET') for s in shops)
        if n >= cfg['min_shops'] and int(obs['market']['prices'].get('TOMATO', 0)) >= cfg['min_price']:
            st['armed'] = True; st['want'] = cfg['n_by_shops'][min(n, len(cfg['n_by_shops']) - 1)]
            st['look'] = _ktt_tape_ops(player, day, min(30, day + 12))
            _KTT_REPORT['armed'] += 1
    if st['armed'] and day == cfg['day'] and len(st['tiles']) < st['want']:
        # seeds: keep enough for this day's substitutions (bought one step ahead)
        have = int(private['seeds'].get('TOMATO', 0))
        need = st['want'] - len(st['tiles'])
        if have < need + cfg.get('seed_pad', 0) and len(market) < 10 and not any(o and o[0] == 'BUY_SEED' and o[1] == 'TOMATO' for o in market):
            q = need - have + cfg.get('seed_pad', 0)
            market = market + [['BUY_SEED', 'TOMATO', q]]; changed = True; _KTT_REPORT['seeds'] += q
        cmds = [list(c) if c else ['PASS'] for c in [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])]
        pos = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
        tom_cmds = sum(1 for c in cmds if c[0] == 'PLANT' and len(c) > 1 and c[1] == 'TOMATO')
        room = have - tom_cmds
        for i, c in enumerate(cmds):
            if room <= 0 or len(st['tiles']) >= st['want']: break
            if i >= len(pos) or c[0] != 'PLANT' or len(c) < 2 or c[1] != 'WHEAT': continue
            x, y = pos[i]
            if farm['tiles'][y][x] is not None: continue
            # the route must keep this plot wet: a WATER on at least every other day until day 28
            ops = st['look'].get((x, y), [])
            wet = {t // 24 for t, op in ops if op == 'WATER' and t >= step}
            wet.add(day)
            dry = any((d not in wet and d + 1 not in wet) for d in range(day, 28))
            if dry:
                _KTT_REPORT['skipped_dry'] += 1; continue
            cmds[i] = ['PLANT', 'TOMATO']; room -= 1
            st['tiles'].add((x, y)); _KTT_REPORT['subs'] += 1; changed = True
        if changed:
            action = dict(action); action['farmer'] = cmds[0]; action['hands'] = cmds[1:]
    if st['tiles']:
        # protect our plots from route digs
        cmds = [list(c) if c else ['PASS'] for c in [action.get('farmer') or ['PASS']] + list(action.get('hands') or [])]
        pos = [tuple(farm['farmer'])] + [tuple(p) for p in farm['hands']]
        dug = False
        for i, c in enumerate(cmds):
            if i < len(pos) and c[0] == 'DIG' and pos[i] in st['tiles']:
                t = farm['tiles'][pos[i][1]][pos[i][0]]
                if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                    cmds[i] = ['PASS']; dug = True; _KTT_REPORT['blocked_dig'] += 1
        if dug:
            action = dict(action); action['farmer'] = cmds[0]; action['hands'] = cmds[1:]; changed = True
        # sell tomatoes from the shed unless someone else already does this step
        shed_t = int(private['shed'].get('TOMATO', 0))
        if shed_t > 0 and len(market) < 10 and not any(o and o[0] == 'SELL' and o[1] == 'TOMATO' for o in market):
            if int(obs['market']['prices'].get('TOMATO', 0)) >= cfg['sell_min']:
                market = market + [['SELL', 'TOMATO', shed_t]]; changed = True; _KTT_REPORT['sold'] += shed_t
    if changed:
        action = dict(action); action['market'] = market
    return action


agent.telemetry = _KTT_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
