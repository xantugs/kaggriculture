
# =====================================================================================
# TOM (offhand, 2026-09-24): a tomato block on the SE quadrant tended by extra hands. The chassis and its copies
# grow almost no tomatoes while the town drains 6/day per pizza shop / farmers market; the pinned oracle prices an
# extra tomato on days 20-27 at ~+$89 of margin against a copy (+4/day flipped 27 of 71 copy games).
# On day D0..D0+stagger-1 (cash permitting) the layer buys the SE quadrant if it is still locked and plants up to N
# tomatoes on empty SE tiles. Each day while plants live it hires W hands at hour HOUR (after the tape's hires),
# hidden from every inner layer (their observation drops those hands; their commands are spliced back in).
# Tomato: planted day p, produces at the ends of days p+7..p+10 (+2 when watered and fertilized that day, else +1),
# dies after two dry days in a row. Workers keep plants alive, water + fertilize on production days, harvest; their
# cargo drops into the shed at midnight. Tomatoes in the shed are sold a few at a time while the price holds.
# =====================================================================================
import copy as _tom_copy

_TOM_ON = True
_TOM_CFG = dict(d0=12, stagger=1, n=20, workers=2, hour=2, cash=9000.0, reserve=2500.0, min_shops=1, fert=True,
                harvest_at=3, deliver_at=6, sell_floor=55.0, sell_step=3, last_plant_day=18, max_wage=400.0)
_TOM_STATE = {}
_TOM_REPORT = dict(tom_on=0, tom_land=0, tom_seeds=0, tom_planted=0, tom_hires=0, tom_wages=0.0, tom_fert_bought=0,
                   tom_harvest_cmds=0, tom_sold=0, tom_lost=0, tom_no_hand=0, tom_errors=0)
_TOM_MOVES = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}
_TOM_PARENT = agent
del agent


def _tom_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _tom_access(board):
    h = board // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def _tom_hide(obs, seat, idx, st=None):
    """Observation without our hands (indices into farm['hands']) and, once active, without the tomato block."""
    foot = st is not None and st.get('active')
    if not idx and not foot:
        return obs
    s = set(idx)
    o2 = _tom_copy.copy(obs)
    farms = list(obs['farms']); f2 = _tom_copy.copy(farms[seat])
    if foot:
        rows = [list(r) for r in farms[seat]['tiles']]
        if st.get('bought'):
            for (x, y) in _tom_se(len(rows)):
                if (x, y) not in _tom_access(len(rows)):
                    rows[y][x] = 'LOCKED'
            f2['unlocked_quadrants'] = [q for q in farms[seat].get('unlocked_quadrants') or [] if q != 'SE']
        else:
            for (x, y) in st['plan']:
                t = rows[y][x]
                if isinstance(t, dict) and t.get('crop') == 'TOMATO':
                    rows[y][x] = None
        f2['tiles'] = rows
    f2['hands'] = [h for k, h in enumerate(farms[seat]['hands']) if k not in s]
    f2['hires_today'] = max(0, int(farms[seat].get('hires_today', 0)) - len(s))
    farms[seat] = f2; o2['farms'] = farms
    p2 = _tom_copy.copy(obs['private'])
    p2['inventories'] = [inv for k, inv in enumerate(obs['private'].get('inventories') or []) if k - 1 not in s]
    o2['private'] = p2
    return o2


def _tom_se(board):
    h = board // 2
    return [(x, y) for y in range(h, board) for x in range(h, board)]


def _tom_prod_days(pd):
    return range(pd + 7, pd + 11)


def _tom_task(tile, pos, day, st, carried_f):
    """Command a worker standing on ``pos`` should issue there, or None."""
    if pos in st['plan'] and st['plan'][pos] <= day <= _TOM_CFG['last_plant_day'] and pos not in st['tiles']:
        if tile is None:
            return ['PLANT', 'TOMATO']
        if isinstance(tile, dict) and tile.get('kind') == 'WEED':
            return ['DIG']
    if not (isinstance(tile, dict) and tile.get('crop') == 'TOMATO' and pos in st['tiles']):
        return None
    pd = int(tile['planted_day']); yu = int(tile.get('yield_units', 0))
    prod = list(_tom_prod_days(pd))
    fu = int(tile.get('fertilized_until_day', -1))
    if yu > 0 and (yu >= _TOM_CFG['harvest_at'] or day > prod[-1] or (day == prod[-1] and yu >= 2)):
        return ['HARVEST']
    need_water = not tile.get('watered_today') and (int(tile.get('consecutive_unwatered', 0)) >= 1 or day in prod)
    if day > prod[-1]:
        need_water = False
    if _TOM_CFG['fert'] and carried_f > 0 and fu < day and day in prod:
        return ['FERTILIZE']
    if need_water:
        return ['WATER']
    return None


def _tom_todo(tiles, day, st, carried_f):
    out = []
    for pos in list(st['tiles']) + [p for p in st['plan'] if p not in st['tiles']]:
        t = tiles[pos[1]][pos[0]]
        c = _tom_task(t, pos, day, st, carried_f)
        if c:
            out.append((pos, c))
    return out


def agent(observation, configuration=None):
    try:
        step = int(observation['step']); seat = int(observation['player'])
        st = _TOM_STATE.get(seat)
        if step == 0 or st is None or step <= st['step']:
            old = _TOM_STATE.get(seat)
            if old and 'v219_saved' in old:
                globals()['_K_V219_CASH'] = old['v219_saved']
            st = _TOM_STATE[seat] = dict(step=-1, day=-1, mine=[], pending=None, plan={}, tiles=set(), active=False,
                                         need_f={}, claimed={})
        st['step'] = step; day = step // 24; hour = step % 24
        farm = observation['farms'][seat]
        if day != st['day']:
            st.update(day=day, mine=[], pending=None, need_f={}, claimed={})
        if st['pending'] is not None:
            n0, k, w = st['pending']; st['pending'] = None
            if len(farm['hands']) == n0 + k + w:
                st['mine'] = list(range(n0 + k, n0 + k + w)); _TOM_REPORT['tom_hires'] += w
                for j in st['mine']:
                    st['need_f'][j] = st.get('fert_q', 0) // max(1, w)
            else:
                _TOM_REPORT['tom_no_hand'] += 1
        st['mine'] = [j for j in st['mine'] if j < len(farm['hands'])]
    except Exception as e:
        _TOM_REPORT['tom_errors'] += 1; _TOM_REPORT['tom_last_error'] = repr(e)[:160]
        return _TOM_PARENT(observation, configuration)
    inner = _tom_hide(observation, seat, st['mine'], st)
    action = _TOM_PARENT(inner, configuration)
    if not isinstance(action, dict):
        return action
    try:
        c = _TOM_CFG
        board = len(farm['tiles']); tiles = farm['tiles']; priv = observation['private']; prices = observation['market']['prices']
        hands = [list(h) for h in (action.get('hands') or [])]
        market = [list(o) for o in (action.get('market') or [])]
        changed = False
        # --- start: buy land / seeds on the planting days
        if _TOM_ON and not st['active'] and day == c['d0'] and hour == c['hour'] and step < 700:
            shops = observation['town'].get('unlocked_shops') or []
            ok_shops = sum(s in ('PIZZA_SHOP', 'FARMERS_MARKET') for s in shops) >= c['min_shops']
            quads = set(farm.get('unlocked_quadrants') or [])
            land = 0 if 'SE' in quads else 4000
            if ok_shops and len(quads) >= 3 and float(farm['money']) >= c['cash'] + land and len(market) <= 8:
                free = [p for p in _tom_se(board) if p not in _tom_access(board) and
                        (land or tiles[p[1]][p[0]] is None or (isinstance(tiles[p[1]][p[0]], dict) and tiles[p[1]][p[0]].get('kind') == 'WEED'))]
                n = min(c['n'], len(free))
                if n >= 4:
                    st['active'] = True; _TOM_REPORT['tom_on'] += 1
                    per = -(-n // max(1, c['stagger']))
                    for i, p in enumerate(free[:n]):
                        st['plan'][p] = c['d0'] + i // per
                    if land:
                        market.append(['BUY_LAND']); _TOM_REPORT['tom_land'] += 1; st['bought'] = True
                    st['start_hire'] = True
                    g = globals()
                    if '_K_V219_CASH' in g:
                        st['v219_saved'] = g['_K_V219_CASH']; g['_K_V219_CASH'] = 10 ** 9
                    market.append(['BUY_SEED', 'TOMATO', n]); _TOM_REPORT['tom_seeds'] += n
                    changed = True
        live = False
        if st['active']:
            for p in list(st['plan']):
                t = tiles[p[1]][p[0]]
                if isinstance(t, dict) and t.get('crop') == 'TOMATO' and p not in st['tiles']:
                    st['tiles'].add(p); _TOM_REPORT['tom_planted'] += 1
            for p in list(st['tiles']):
                t = tiles[p[1]][p[0]]
                if not (isinstance(t, dict) and t.get('crop') == 'TOMATO'):
                    st['tiles'].discard(p)
                    if day <= int(st['plan'].get(p, 0)) + 10:
                        _TOM_REPORT['tom_lost'] += 1
            live = bool(st['tiles']) or any(d >= day for d in st['plan'].values())
        # --- hire workers for the day
        if st['active'] and live and hour == c['hour'] and not st['mine'] and len(market) <= 8:
            todo = _tom_todo(tiles, day, st, 1)
            if st.pop('start_hire', False):
                todo = [(p, ['PLANT', 'TOMATO']) for p in st['plan']]
            if todo:
                k = sum(1 for o in market if o and o[0] == 'HIRE')
                h0 = int(farm.get('hires_today', 0)) + k
                w = c['workers'] if len(todo) > 8 else 1
                wage = sum(_tom_fib(h0 + i) for i in range(w))
                fert_q = 0
                if c['fert']:
                    fert_q = sum(1 for p in st['tiles'] if day in _tom_prod_days(int(tiles[p[1]][p[0]]['planted_day']))
                                 and int(tiles[p[1]][p[0]].get('fertilized_until_day', -1)) < day)
                cost = wage + fert_q * (float(prices.get('FERTILIZER', 100)) + 2)
                if wage <= c['max_wage'] * w and float(farm['money']) >= cost + c['reserve']:
                    for _ in range(w):
                        market.append(['HIRE'])
                    if fert_q:
                        market.append(['BUY_PRODUCT', 'FERTILIZER', fert_q]); _TOM_REPORT['tom_fert_bought'] += fert_q
                    st['pending'] = (len(farm['hands']), k, w); st['fert_q'] = fert_q
                    _TOM_REPORT['tom_wages'] += wage; changed = True
        # --- drive our workers
        if st['mine']:
            invs = priv.get('inventories') or []
            access = _tom_access(board)
            parent_hire = any(o and o[0] == 'HIRE' for o in market)
            shed_f = int(priv['shed'].get('FERTILIZER', 0))
            seeds = int(priv['seeds'].get('TOMATO', 0))
            cmds = {}
            for n_w, j in enumerate(st['mine']):
                me = tuple(farm['hands'][j]); inv = invs[j + 1] if len(invs) > j + 1 else {}
                cf = int(inv.get('FERTILIZER', 0))
                cmd = None
                if st['need_f'].get(j, 0) > 0 and me in access and shed_f > 0:
                    q = min(st['need_f'][j], shed_f); cmd = ['PICKUP', 'FERTILIZER', q]; st['need_f'][j] = 0; shed_f -= q
                cargo = int(inv.get('TOMATO', 0))
                if cmd is None and cargo and me in access:
                    cmd = ['PLACE', 'TOMATO', cargo]
                if cmd is None and cargo >= _TOM_CFG.get('deliver_at', 6) or (cmd is None and cargo and hour >= 21):
                    ax, ay = min(access, key=lambda a: abs(a[0] - me[0]) + abs(a[1] - me[1]))
                    cmd = [('EAST' if ax > me[0] else 'WEST')] if ax != me[0] else [('SOUTH' if ay > me[1] else 'NORTH')]
                if cmd is None:
                    here = _tom_task(tiles[me[1]][me[0]], me, day, st, cf)
                    if here and st['claimed'].get(me, j) == j and not (here[0] == 'PLANT' and seeds <= 0):
                        cmd = here; st['claimed'][me] = j
                        if here[0] == 'PLANT':
                            seeds -= 1
                        if here[0] == 'HARVEST':
                            _TOM_REPORT['tom_harvest_cmds'] += 1
                if cmd is None:
                    todo = [(p, t) for p, t in _tom_todo(tiles, day, st, cf) if st['claimed'].get(p, j) == j and p != me]
                    # split the block between workers: worker n takes tiles whose index % W == n first
                    order = sorted(st['plan'])
                    mine_first = [(p, t) for p, t in todo if order.index(p) % len(st['mine']) == n_w] if p_in(order, todo) else []
                    pool = mine_first or todo
                    if pool:
                        tgt = min(pool, key=lambda v: abs(v[0][0] - me[0]) + abs(v[0][1] - me[1]))[0]
                        st['claimed'][tgt] = j
                        if tgt[0] != me[0]:
                            cmd = ['EAST' if tgt[0] > me[0] else 'WEST']
                        else:
                            cmd = ['SOUTH' if tgt[1] > me[1] else 'NORTH']
                if cmd is None:
                    cmd = ['PASS']
                if parent_hire:
                    if cmd[0] in _TOM_MOVES:
                        dx, dy = _TOM_MOVES[cmd[0]]
                        if (me[0] + dx, me[1] + dy) in access:
                            cmd = ['PASS']
                    if me in access and cmd[0] not in _TOM_MOVES:
                        for mv, (dx, dy) in _TOM_MOVES.items():
                            nx, ny = me[0] + dx, me[1] + dy
                            if 0 <= nx < board and 0 <= ny < board and (nx, ny) not in access:
                                cmd = [mv]; break
                cmds[j] = cmd
            for j in sorted(cmds):
                while len(hands) < j:
                    hands.append(['PASS'])
                hands.insert(j, cmds[j])
            changed = True
        # --- sell tomatoes a few at a time
        if st['active'] and len(market) < 10:
            have = int(priv['shed'].get('TOMATO', 0)) - sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ['SELL', 'TOMATO'])
            price = float(prices.get('TOMATO', 0))
            if have > 0 and (price >= c['sell_floor'] or step >= 700):
                q = have if step >= 700 else min(have, c['sell_step'])
                market.append(['SELL', 'TOMATO', q]); _TOM_REPORT['tom_sold'] += q; changed = True
        if changed:
            action = dict(action); action['hands'] = hands; action['market'] = market[:10]
    except Exception as e:
        import traceback
        _TOM_REPORT['tom_errors'] += 1
        _TOM_REPORT['tom_last_error'] = repr(e)[:80] + ' @ ' + traceback.format_exc().strip().splitlines()[-3].strip()[:120]
    return action


def p_in(order, todo):
    return all(p in order for p, _ in todo)


agent.telemetry = _TOM_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
