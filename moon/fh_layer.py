
# =====================================================================================
# FH (offhand, 2026-09-24): a fertilizer hand. The chassis is labor-bound and leaves ~230 wheat waterings, ~40
# carrot waterings and ~10 strawberry productions per game unfertilized (+1 instead of +2), while late fertilizer
# sells for $15-60. On days D0..D1, at hour HOUR (after the tape's own hires) one extra hand is hired when a greedy
# fertilizing route for the rest of the day is worth more than its wage plus the fertilizer. The fertilizer is
# bought the same step and picked up at the shed on the hand's first step. The hand is hidden from every inner
# layer (their observation has it removed) and its command is spliced back into the hands list at its index.
# Targets (gain = extra units from one FERTILIZE today, before the tape's WATER on that tile when that matters):
#   wheat/carrot in the watering window (ages 2..max_yield_day) or carrot at age 1, strawberry/tomato productions
#   on days d..d+2 that the tile's fertilizer does not cover.
# =====================================================================================
import copy as _fh_copy

_FH_ON = True
_FH_CFG = dict(d0=5, d1=28, hour=2, margin=60.0, max_carry=12, wheat_age1=False, px=dict(WHEAT=1.0, CARROT=1.0, STRAWBERRY=0.8, TOMATO=0.8),
               fert_extra=2, max_hands=1)
_FH_STATE = {}
_FH_REPORT = dict(fh_days=0, fh_hires=0, fh_fert=0, fh_units=0.0, fh_bought=0, fh_cost=0.0, fh_plan_value=0.0,
                  fh_no_hand=0, fh_skipped=0, fh_errors=0)
_FH_CROP = {'WHEAT': (4, 6, False), 'CARROT': (3, 4, False), 'STRAWBERRY': (10, 4, True), 'TOMATO': (8, 4, True)}
_FH_ONG = {'STRAWBERRY': (10, 2, 4), 'TOMATO': (8, 1, 4)}
_FH_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_FH_PARENT = agent
del agent


def _fh_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _fh_access(board):
    h = board // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def _fh_tape_ops(obs, action, t_end):
    """{(x, y): [(t, op)]} for the tape's non-move commands from this step (with ``action``) to ``t_end``."""
    seat = int(obs['player']); step = int(obs['step'])
    farm = obs['farms'][seat]; board = len(farm['tiles']); half = board // 2
    positions = [list(farm['farmer'])] + [list(h) for h in farm['hands']]
    out = {}
    for t in range(step, min(t_end, 719) + 1):
        act = action if t == step else _ca_tape(seat, t)
        units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
        for i in range(len(positions)):
            cmd = units[i] if i < len(units) and units[i] else ['PASS']
            if cmd[0] in _FH_MOVES:
                dx, dy = _FH_MOVES[cmd[0]]
                nx, ny = positions[i][0] + dx, positions[i][1] + dy
                if 0 <= nx < board and 0 <= ny < board:
                    positions[i] = [nx, ny]
            elif cmd[0] != 'PASS':
                out.setdefault(tuple(positions[i]), []).append((t, cmd[0]))
        for _ in range(sum(1 for o in (act.get('market') or []) if o and o[0] == 'HIRE')):
            positions.append(_ca_spawn(positions, board))
        if t % 24 == 23:
            positions = [[half - 1, half - 1]]
    return out


def _fh_gain(tile, day, t_arrive, ops):
    """Extra units from a FERTILIZE on this tile at step ``t_arrive`` (day ``day``)."""
    crop = tile.get('crop')
    if crop not in _FH_CROP:
        return 0
    pd = int(tile['planted_day']); fu = int(tile.get('fertilized_until_day', -1)); new = day + 2
    if fu >= new:
        return 0
    age = day - pd
    if crop in _FH_ONG:
        fyd, iv, mx = _FH_ONG[crop]
        g = 0
        for e in range(max(day, fu + 1), new + 1):
            ds = e + 1 - pd - fyd
            if ds < 0 or ds % iv or ds // iv + 1 > mx:
                continue
            # production at the end of day e needs a WATER that day
            if any(t // 24 == e and op == 'WATER' for t, op in ops) or (e == day and tile.get('watered_today')):
                g += 1
        return g
    myd, cap, _ = _FH_CROP[crop]
    lo = (myd + 1) // 2
    if age < (1 if crop == 'CARROT' or _FH_CFG['wheat_age1'] else lo) or age > myd:
        return 0
    g = 0
    for e in range(max(day, fu + 1), new + 1):
        a = e - pd
        if not lo <= a <= myd:
            continue
        if e == day:
            if tile.get('watered_today'):
                continue
            if not any(t // 24 == e and op == 'WATER' and t > t_arrive for t, op in ops):
                continue
        elif not any(t // 24 == e and op == 'WATER' for t, op in ops):
            continue
        g += 1
    # harvest before the window ends forfeits nothing already counted (waterings are checked explicitly)
    return min(g, max(0, cap - int(tile.get('yield_units', 0))))


def _fh_plan(tiles, day, start, t0, t_end, ops, prices, carry, done):
    """Greedy route: list of (pos, t_fert, gain, value) visiting best value/step targets from ``start`` at step t0."""
    px = _FH_CFG['px']
    plan = []; pos = tuple(start); t = t0; left = carry; used = set(done)
    while left > 0 and t <= t_end:
        best = None
        for y, row in enumerate(tiles):
            for x, tl in enumerate(row):
                if (x, y) in used or not (isinstance(tl, dict) and tl.get('kind') == 'PLANT'):
                    continue
                dist = abs(x - pos[0]) + abs(y - pos[1])
                ta = t + dist
                if ta > t_end:
                    continue
                g = _fh_gain(tl, day, ta, ops.get((x, y), []))
                if g <= 0:
                    continue
                v = g * float(prices.get(tl['crop'], 40)) * px.get(tl['crop'], 1.0)
                sc = v / (dist + 1)
                if best is None or sc > best[0]:
                    best = (sc, (x, y), ta, g, v)
        if best is None:
            break
        _, p, ta, g, v = best
        plan.append((p, ta, g, v)); used.add(p); pos = p; t = ta + 1; left -= 1
    return plan


def _fh_hide(obs, seat, j):
    o2 = _fh_copy.copy(obs)
    farms = list(obs['farms']); f2 = _fh_copy.copy(farms[seat])
    f2['hands'] = [h for k, h in enumerate(farms[seat]['hands']) if k != j]
    f2['hires_today'] = max(0, int(farms[seat].get('hires_today', 0)) - 1)
    farms[seat] = f2; o2['farms'] = farms
    p2 = _fh_copy.copy(obs['private'])
    p2['inventories'] = [inv for k, inv in enumerate(obs['private'].get('inventories') or []) if k != j + 1]
    o2['private'] = p2
    return o2


def agent(observation, configuration=None):
    try:
        step = int(observation['step']); seat = int(observation['player'])
        st = _FH_STATE.get(seat)
        if step == 0 or st is None or step <= st['step']:
            st = _FH_STATE[seat] = dict(step=-1, day=-1, j=None, pending=None, done=set(), plan=[], ops={})
        st['step'] = step; day = step // 24; hour = step % 24
        if day != st['day']:
            st.update(day=day, j=None, pending=None, done=set(), plan=[], ops={})
        farm = observation['farms'][seat]
        if st['pending'] is not None:
            n0, k = st['pending']; st['pending'] = None
            if len(farm['hands']) == n0 + k + 1:
                st['j'] = n0 + k; _FH_REPORT['fh_hires'] += 1
            else:
                _FH_REPORT['fh_no_hand'] += 1
        j = st['j']
        if j is not None and j >= len(farm['hands']):
            st['j'] = j = None
    except Exception as e:
        _FH_REPORT['fh_errors'] += 1; _FH_REPORT['fh_last_error'] = repr(e)[:160]
        return _FH_PARENT(observation, configuration)
    inner = _fh_hide(observation, seat, j) if j is not None else observation
    action = _FH_PARENT(inner, configuration)
    if not isinstance(action, dict):
        return action
    try:
        board = len(farm['tiles']); priv = observation['private']; prices = observation['market']['prices']
        hands = [list(h) for h in (action.get('hands') or [])]
        market = [list(o) for o in (action.get('market') or [])]
        if j is not None:
            me = tuple(farm['hands'][j]); invs = priv.get('inventories') or []
            inv = invs[j + 1] if len(invs) > j + 1 else {}
            have = int(inv.get('FERTILIZER', 0))
            parent_hire = any(o and o[0] == 'HIRE' for o in market)
            access = set(_fh_access(board))
            cmd = ['PASS']
            shed_f = int(priv['shed'].get('FERTILIZER', 0))
            if st.get('need', 0) > 0 and shed_f > 0:
                if me in access:
                    cmd = ['PICKUP', 'FERTILIZER', min(st['need'], shed_f)]
                elif have == 0:
                    tx, ty = min(access, key=lambda a: abs(a[0] - me[0]) + abs(a[1] - me[1]))
                    cmd = [('EAST' if tx > me[0] else 'WEST') if tx != me[0] else ('SOUTH' if ty > me[1] else 'NORTH')]
            if cmd == ['PASS'] and have > 0:
                tl = farm['tiles'][me[1]][me[0]]
                if me not in st['done'] and isinstance(tl, dict) and tl.get('kind') == 'PLANT' and \
                        _fh_gain(tl, day, step, st['ops'].get(me, [])) > 0:
                    g = _fh_gain(tl, day, step, st['ops'].get(me, []))
                    cmd = ['FERTILIZE']; st['done'].add(me)
                    _FH_REPORT['fh_fert'] += 1; _FH_REPORT['fh_units'] += g
                else:
                    plan = _fh_plan(farm['tiles'], day, me, step, day * 24 + 23, st['ops'], prices, have, st['done'])
                    if plan:
                        tx, ty = plan[0][0]
                        if tx != me[0]:
                            cmd = ['EAST' if tx > me[0] else 'WEST']
                        elif ty != me[1]:
                            cmd = ['SOUTH' if ty > me[1] else 'NORTH']
            if parent_hire and cmd[0] not in _FH_MOVES:
                # never stand on a shed-access tile while the tape hires (it would move the new hand's spawn)
                if me in access:
                    for mv, (dx, dy) in _FH_MOVES.items():
                        nx, ny = me[0] + dx, me[1] + dy
                        if 0 <= nx < board and 0 <= ny < board and (nx, ny) not in access:
                            cmd = [mv]; break
            elif parent_hire and cmd[0] in _FH_MOVES:
                dx, dy = _FH_MOVES[cmd[0]]
                if (me[0] + dx, me[1] + dy) in access:
                    cmd = ['PASS'] if me not in access else cmd
            if cmd[0] == 'PICKUP':
                st['need'] = 0
            while len(hands) < j:
                hands.append(['PASS'])
            hands.insert(j, cmd)
            action = dict(action); action['hands'] = hands
        elif _FH_ON and _FH_CFG['d0'] <= day <= _FH_CFG['d1'] and hour == _FH_CFG['hour'] and len(market) <= 8:
            _FH_REPORT['fh_days'] += 1
            view = inner
            st['ops'] = _fh_tape_ops(view, action, day * 24 + 71)
            k = sum(1 for o in market if o and o[0] == 'HIRE')
            fprice = float(prices.get('FERTILIZER', 100)) + 1
            start = _fh_access(board)[0]
            plan = _fh_plan(farm['tiles'], day, start, step + 2, day * 24 + 23, st['ops'], prices, _FH_CFG['max_carry'], set())
            value = sum(p[3] for p in plan)
            wage = _fh_fib(int(farm.get('hires_today', 0)) + k)
            n = len(plan)
            cost = wage + (n + _FH_CFG['fert_extra']) * fprice
            if n and value - cost > _FH_CFG['margin'] and float(farm['money']) > cost + 200:
                q = n + _FH_CFG['fert_extra']
                market.append(['HIRE']); market.append(['BUY_PRODUCT', 'FERTILIZER', q])
                st['pending'] = (len(farm['hands']), k); st['need'] = q
                _FH_REPORT['fh_bought'] += q; _FH_REPORT['fh_cost'] += cost; _FH_REPORT['fh_plan_value'] += value
                action = dict(action); action['market'] = market
            else:
                _FH_REPORT['fh_skipped'] += 1
    except Exception as e:
        import traceback
        _FH_REPORT['fh_errors'] += 1
        _FH_REPORT['fh_last_error'] = repr(e)[:80] + ' @ ' + traceback.format_exc().strip().splitlines()[-3].strip()[:120]
    return action


agent.telemetry = _FH_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
