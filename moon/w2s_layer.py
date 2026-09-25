
# =====================================================================================
# W2S (offhand, 2026-09-24): early strawberries on wheat tiles. Pinned on games vs 2800+ teams, one more
# strawberry sold on days 14-19 is worth ~+$175 of margin against a chassis copy (+$32 to us, -$142 to the
# rival, whose ~200 later strawberries all sell lower) and ~+$142 against other strong farms. A strawberry
# planted on day d bears at the ends of days d+9, d+11, d+13, d+15 (+2 when watered and fertilized). In the
# window [D0, D1] up to MAX tape wheat plantings are planted as strawberries instead, when: the tape keeps
# visiting that tile at least every other day for the plant's life (so it is watered), cash after the extra
# seed covers the tape's purchases of the next 24 steps plus RESERVE, and wheat in hand covers two days of
# feeding. Visits to a swapped tile: a no-op PLANT becomes WATER, a WATER on >= HARVEST_AT units (or any
# visit after the last production) becomes HARVEST.
# =====================================================================================
_W2S_ON = True
_W2S_CFG = dict(d0=5, d1=8, max=3, reserve=600, spend_h=0, harvest_at=3, feed_days=2, gap=1, pool=1, sell=True, sell_min=2, lookahead=True, topup=0)
_W2S_STATE = {}
_W2S_REPORT = dict(w2s_swaps=0, w2s_seed=0, w2s_conv_h=0, w2s_conv_w=0, w2s_harvested=0, w2s_lost=0,
                   w2s_cash_block=0, w2s_feed_block=0, w2s_visit_block=0, w2s_sold=0, w2s_errors=0)
_W2S_MOVES = ("NORTH", "SOUTH", "EAST", "WEST")
_W2S_SEED = {'WHEAT': 10, 'CARROT': 20, 'TOMATO': 50, 'STRAWBERRY': 100, 'MELON': 80}
_W2S_ANI = {'SHEEP': 500, 'COW': 400, 'GOOSE': 300}
_W2S_PARENT = agent
del agent


def _w2s_spend(seat, step, horizon, prices):
    spend = 0; hires = {}
    for t in range(step + 1, min(719, step + horizon) + 1):
        for o in _ca_tape(seat, t).get('market', []) or []:
            if not o:
                continue
            if o[0] == 'BUY_SEED' and len(o) >= 3:
                spend += int(o[2]) * _W2S_SEED.get(o[1], 100)
            elif o[0] == 'BUY_ANIMAL' and len(o) >= 3:
                spend += int(o[2]) * _W2S_ANI.get(o[1], 500)
            elif o[0] == 'BUY_PRODUCT' and len(o) >= 3:
                spend += int(o[2]) * (int(prices.get(o[1], 50)) + 5)
            elif o[0] == 'BUY_LAND':
                spend += 1000
            elif o[0] == 'HIRE':
                d = t // 24; spend += _v219_fib(hires.get(d, 0)); hires[d] = hires.get(d, 0) + 1
    return spend


def _w2s_tended(obs, action, pos, day):
    """True when, for days day+1 .. day+15, the tape puts a unit on ``pos`` at least every other day and never
    plans anything there but wheat (a later strawberry/carrot/building on that tile would be displaced)."""
    seat = int(obs['player']); step = int(obs['step'])
    farm = obs['farms'][seat]; board = len(farm['tiles']); half = board // 2
    positions = [list(farm['farmer'])] + [list(h) for h in farm['hands']]
    days = set()
    for t in range(step, min(719, (day + 16) * 24 - 1) + 1):
        act = action if t == step else _ca_tape(seat, t)
        units = [act.get('farmer') or ['PASS']] + list(act.get('hands') or [])
        for i in range(len(positions)):
            cmd = units[i] if i < len(units) and units[i] else ['PASS']
            if cmd[0] in _CA_MOVES:
                dx, dy = _CA_MOVES[cmd[0]]
                nx, ny = positions[i][0] + dx, positions[i][1] + dy
                if 0 <= nx < board and 0 <= ny < board:
                    positions[i] = [nx, ny]
            elif tuple(positions[i]) == pos and t > step:
                if cmd[0] in ('BUILD_COOP', 'BUILD_PASTURE', 'DIG') or (cmd[0] == 'PLANT' and cmd[1:2] != ['WHEAT']):
                    return False
                days.add(t // 24)
        for _ in range(sum(1 for o in (act.get('market') or []) if o and o[0] == 'HIRE')):
            positions.append(_ca_spawn(positions, board))
        if t % 24 == 23:
            positions = [[half - 1, half - 1]]
    gap = 0
    for d in range(day + 1, min(29, day + 15) + 1):
        gap = 0 if d in days else gap + 1
        if gap > _W2S_CFG['gap']:
            return False
    return True


def agent(observation, configuration=None):
    action = _W2S_PARENT(observation, configuration)
    try:
        step = int(observation['step']); seat = int(observation['player'])
        st = _W2S_STATE.get(seat)
        if step == 0 or st is None or step <= st['step']:
            st = _W2S_STATE[seat] = dict(step=-1, tiles={}, swaps=0, pool=0, credit=0)
        st['step'] = step
        if not isinstance(action, dict) or step > 717 or not (_W2S_ON or st['tiles'] or st['credit']):
            return action
        c = _W2S_CFG; day = step // 24
        farm = observation['farms'][seat]; tiles = farm['tiles']; priv = observation['private']
        prices = observation['market']['prices']
        positions = [tuple(farm['farmer'])] + [tuple(h) for h in farm['hands']]
        units = [list(action.get('farmer') or ['PASS'])] + [list(u) for u in (action.get('hands') or [])]
        market = [list(o) for o in (action.get('market') or [])]
        changed = False
        # 1. tend swapped tiles
        for pos, planted in list(st['tiles'].items()):
            tile = tiles[pos[1]][pos[0]]
            if not (isinstance(tile, dict) and tile.get('crop') == 'STRAWBERRY' and int(tile.get('planted_day', -9)) == planted):
                st['tiles'].pop(pos, None); _W2S_REPORT['w2s_lost'] += 1
                continue
            here = [i for i, p in enumerate(positions) if p == pos and i < len(units)]
            if not here:
                continue
            i = here[0]; cmd = units[i]; yu = int(tile.get('yield_units', 0)); age = day - planted
            if not cmd or cmd[0] in _W2S_MOVES:
                continue
            if cmd[0] == 'HARVEST':
                _W2S_REPORT['w2s_harvested'] += yu; st['credit'] += yu
                continue
            over = age >= 16
            if yu > 0 and (over or (cmd[0] in ('WATER', 'PLANT', 'PASS') and yu >= c['harvest_at'])):
                units[i] = ['HARVEST']; _W2S_REPORT['w2s_conv_h'] += 1; _W2S_REPORT['w2s_harvested'] += yu; st['credit'] += yu; changed = True
            elif cmd[0] in ('PLANT', 'PASS') and not tile.get('watered_today') and not over:
                units[i] = ['WATER']; _W2S_REPORT['w2s_conv_w'] += 1; changed = True
        # 1b. sell the swapped tiles' harvest as soon as it is in the shed
        if c.get('sell') and st['credit'] > 0 and len(market) < 10 and int(prices.get('STRAWBERRY', 0)) >= c.get('sell_min', 2):
            view_action = {'farmer': units[0], 'hands': units[1:], 'market': market}
            stock = int(projected_shed(view_action, FarmView(observation)).get('STRAWBERRY', 0))
            selling = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ['SELL', 'STRAWBERRY'])
            q = min(st['credit'], stock - selling)
            if q > 0:
                market.insert(0, ['SELL', 'STRAWBERRY', q]); st['credit'] -= q; _W2S_REPORT['w2s_sold'] += q; changed = True
        if not _W2S_ON or not c['d0'] <= day <= c['d1'] or st['swaps'] >= c['max']:
            if changed:
                action = dict(action); action['farmer'] = units[0]; action['hands'] = units[1:]; action['market'] = market[:10]
            return action
        # 2. swap tape wheat plantings (seeds from the pool bought earlier)
        have = int(priv['seeds'].get('STRAWBERRY', 0)) - sum(1 for u in units if u[:2] == ['PLANT', 'STRAWBERRY'])
        spend = None
        for i, cmd in enumerate(units):
            if cmd[:2] != ['PLANT', 'WHEAT'] or i >= len(positions) or have <= 0 or st['pool'] <= 0 or st['swaps'] >= c['max']:
                continue
            pos = positions[i]
            if tiles[pos[1]][pos[0]] is not None:
                continue
            if c['feed_days'] and _ca_wheat_total(observation) < _ca_feed_need(seat, step, c['feed_days']):
                _W2S_REPORT['w2s_feed_block'] += 1; break
            if not _w2s_tended(observation, action, pos, day):
                _W2S_REPORT['w2s_visit_block'] += 1; continue
            units[i] = ['PLANT', 'STRAWBERRY']; have -= 1; st['pool'] -= 1; st['swaps'] += 1
            st['tiles'][pos] = day; _W2S_REPORT['w2s_swaps'] += 1; changed = True
            if c.get('topup') and len(market) < 10:
                market.append(['BUY_PRODUCT', 'WHEAT', c['topup']])
        # 3. keep a seed pool while swaps remain (paid only when cash covers the tape's next day of purchases)
        nxt = _ca_tape(seat, step + 1) if c.get('lookahead') else None
        soon = nxt is None or any(u and u[:2] == ['PLANT', 'WHEAT'] for u in [nxt.get('farmer')] + list(nxt.get('hands') or []))
        if soon and c['feed_days'] and _ca_wheat_total(observation) < _ca_feed_need(seat, step + 1, c['feed_days']):
            soon = False
        if soon and st['swaps'] < c['max'] and st['pool'] < c['pool'] and day <= c['d1'] and len(market) < 10 and step % 24 < 23:
            q = min(c['pool'] - st['pool'], c['max'] - st['swaps'])
            spend = (_w2s_spend(seat, step, c['spend_h'], prices) if c['spend_h'] else 0) + sum(int(o[2]) * _W2S_SEED.get(o[1], 100) for o in market if o[0] == 'BUY_SEED' and len(o) >= 3)
            if int(farm['money']) - 100 * q - spend >= c['reserve']:
                market.append(['BUY_SEED', 'STRAWBERRY', q]); st['pool'] += q; _W2S_REPORT['w2s_seed'] += q; changed = True
            else:
                _W2S_REPORT['w2s_cash_block'] += 1
        if changed:
            action = dict(action); action['farmer'] = units[0]; action['hands'] = units[1:]; action['market'] = market[:10]
    except Exception as e:
        import traceback
        _W2S_REPORT['w2s_errors'] += 1; _W2S_REPORT['w2s_last_error'] = repr(e)[:80] + ' @ ' + traceback.format_exc().strip().splitlines()[-3].strip()[:120]
    return action


agent.telemetry = _W2S_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
