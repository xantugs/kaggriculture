
# =====================================================================================
# ST (offhand, 2026-09-24): late strawberry batch -> tomatoes. The tape plants ~13 strawberries on day 11 (the new
# SW quadrant); they bear on days 21-27, exactly when the strawberry market crashes (median noon price 211 on day
# 16, 26-45 on days 23-24 in games vs 2800+ teams). A tomato planted the same day bears at the ends of days 18-21
# (+2 per day when watered and fertilized, the tile holds at most 4) and dies after day 22, so it is sold before
# the crash. The tape's seed buys and plantings of the swap days are rewritten one for one, inner layers are shown
# the tomato seeds as strawberry seeds, a WATER visit on a tile holding >= HARVEST_AT tomatoes (or any visit once
# production is over) becomes a HARVEST, and harvested tomatoes are sold from the shed.
# =====================================================================================
_ST_ON = True
_ST_CFG = dict(d0=11, d1=11, crop='TOMATO', harvest_at=3, sell_min=2, max_swaps=99)
_ST_STATE = {}
_ST_REPORT = dict(st_swaps=0, st_seed_swapped=0, st_conv=0, st_harvested=0, st_sold=0, st_lost=0, st_errors=0)
_ST_MOVES = ("NORTH", "SOUTH", "EAST", "WEST")
_ST_PARENT = agent
del agent


def _st_view(obs, st):
    """Observation for inner layers: pool tomato seeds shown as strawberry seeds."""
    pool = st['pool']
    if pool <= 0:
        return obs
    priv = obs['private']
    seeds = dict(priv['seeds'])
    k = min(pool, int(seeds.get(_ST_CFG['crop'], 0)))
    if k <= 0:
        return obs
    seeds[_ST_CFG['crop']] = int(seeds.get(_ST_CFG['crop'], 0)) - k
    seeds['STRAWBERRY'] = int(seeds.get('STRAWBERRY', 0)) + k
    p2 = dict(priv); p2['seeds'] = seeds
    o2 = dict(obs); o2['private'] = p2
    return o2


def agent(observation, configuration=None):
    step = int(observation['step']); seat = int(observation['player'])
    st = _ST_STATE.get(seat)
    if step == 0 or st is None or step <= st['step']:
        st = _ST_STATE[seat] = dict(step=-1, pool=0, tiles={}, credit=0, swaps=0)
    st['step'] = step
    try:
        inner_obs = _st_view(observation, st) if _ST_ON or st['pool'] else observation
    except Exception:
        _ST_REPORT['st_errors'] += 1; inner_obs = observation
    action = _ST_PARENT(inner_obs, configuration)
    try:
        if not isinstance(action, dict) or step > 717 or not (_ST_ON or st['tiles'] or st['credit']):
            return action
        c = _ST_CFG; crop = c['crop']
        day = step // 24
        farm = observation['farms'][seat]; tiles = farm['tiles']; priv = observation['private']
        positions = [tuple(farm['farmer'])] + [tuple(h) for h in farm['hands']]
        units = [list(action.get('farmer') or ['PASS'])] + [list(u) for u in (action.get('hands') or [])]
        market = [list(o) for o in (action.get('market') or [])]
        changed = False
        # 1. swapped tiles: bookkeeping, early harvests
        for pos, planted in list(st['tiles'].items()):
            tile = tiles[pos[1]][pos[0]]
            if not (isinstance(tile, dict) and tile.get('crop') == crop and int(tile.get('planted_day', -9)) == planted):
                st['tiles'].pop(pos, None); _ST_REPORT['st_lost'] += 1
                continue
            here = [i for i, p in enumerate(positions) if p == pos and i < len(units)]
            if not here:
                continue
            i = here[0]; cmd = units[i]; yu = int(tile.get('yield_units', 0)); age = day - planted
            if yu <= 0 or not cmd or cmd[0] in _ST_MOVES:
                continue
            if cmd[0] == 'HARVEST':
                st['credit'] += yu; _ST_REPORT['st_harvested'] += yu
                continue
            over = age >= 11
            if (cmd[0] == 'WATER' and (yu >= c['harvest_at'] or over)) or (cmd[0] == 'PASS') or (over and cmd[0] in ('FERTILIZE', 'WATER')):
                units[i] = ['HARVEST']; st['credit'] += yu
                _ST_REPORT['st_harvested'] += yu; _ST_REPORT['st_conv'] += 1; changed = True
        # 2. swap the tape's plantings (seeds bought by the swap are in the pool)
        if st['pool'] > 0:
            have = int(priv['seeds'].get(crop, 0)) - sum(1 for u in units if u[:2] == ['PLANT', crop])
            for i, cmd in enumerate(units):
                if cmd[:2] != ['PLANT', 'STRAWBERRY'] or i >= len(positions) or have <= 0 or st['pool'] <= 0:
                    continue
                pos = positions[i]
                if tiles[pos[1]][pos[0]] is not None:
                    continue
                units[i] = ['PLANT', crop]; have -= 1; st['pool'] -= 1
                st['tiles'][pos] = day; st['swaps'] += 1; _ST_REPORT['st_swaps'] += 1; changed = True
        # 3. swap the tape's seed buys on the swap days
        if _ST_ON and c['d0'] <= day <= c['d1']:
            for o in market:
                if len(o) >= 3 and o[:2] == ['BUY_SEED', 'STRAWBERRY'] and st['swaps'] + st['pool'] < c['max_swaps']:
                    q = min(int(o[2]), c['max_swaps'] - st['swaps'] - st['pool'])
                    if q <= 0:
                        continue
                    if q < int(o[2]):
                        market.append(['BUY_SEED', 'STRAWBERRY', int(o[2]) - q])
                    o[1] = crop; o[2] = q
                    st['pool'] += q; _ST_REPORT['st_seed_swapped'] += q; changed = True
        # 4. sell credited tomatoes
        if st['credit'] > 0 and len(market) < 10 and int(observation['market']['prices'].get(crop, 0)) >= c['sell_min']:
            view_action = {'farmer': units[0], 'hands': units[1:], 'market': market}
            stock = int(projected_shed(view_action, FarmView(observation)).get(crop, 0))
            selling = sum(int(o[2]) for o in market if len(o) >= 3 and o[:2] == ['SELL', crop])
            q = min(st['credit'], stock - selling)
            if q > 0:
                market.insert(0, ['SELL', crop, q]); st['credit'] -= q; _ST_REPORT['st_sold'] += q; changed = True
        if changed:
            action = dict(action); action['farmer'] = units[0]; action['hands'] = units[1:]; action['market'] = market[:10]
    except Exception as e:
        _ST_REPORT['st_errors'] += 1; _ST_REPORT['st_last_error'] = repr(e)[:160]
    return action


agent.telemetry = _ST_REPORT
agent = globals().pop('agent')
globals().pop('kaggle_submission_agent', None)
kaggle_submission_agent = agent
