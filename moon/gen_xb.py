"""Generate xb_layer.py (extra crop block on SE: strawberry or tomato) from the arena's tomato block layer."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', 'arena', 'layers', 'tblock.py'), encoding='utf-8').read()
s = src.replace('_TB_', '_XB_').replace('_tb_', '_xb_').replace('__TBCFG__', '__XBCFG__')


def rep(a, b):
    global s
    assert a in s, a[:70]
    s = s.replace(a, b, 1)


def span(a, b, new):
    global s
    i = s.index(a); j = s.index(b)
    s = s[:i] + new + s[j:]


rep("# TBLOCK: a fertilized tomato block on SE land that the route leaves idle.",
    "# XB: an extra crop block (strawberry or tomato) on SE land, generalised from TBLOCK.\n"
    "# Committed when the crop's price shows unmet town demand; sells exactly what its crew delivers.")
rep("_XB_TOMATO_SHOPS = ('PIZZA_SHOP', 'FARMERS_MARKET')",
    "_XB_SHOP_GOODS = {'BAKERY': ('EGG', 'WHEAT'), 'PIZZA_SHOP': ('MILK', 'TOMATO', 'WHEAT'),\n"
    "                  'BRUNCH_SPOT': ('EGG', 'WHEAT', 'STRAWBERRY'), 'YARN_STORE': ('WOOL',),\n"
    "                  'ICE_CREAM_SHOP': ('STRAWBERRY', 'MILK', 'WHEAT'), 'PET_CAFE': ('CARROT',),\n"
    "                  'SMOOTHIE_SHOP': ('STRAWBERRY', 'MILK'), 'FARMERS_MARKET': ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY')}\n"
    "_XB_CROP = {'TOMATO': (8, 1, 50), 'STRAWBERRY': (10, 2, 100)}   # first yield age, interval, seed cost")

span('def _xb_decide(obs, player, st):', 'def _xb_tile_tasks(obs, st, day):', '''def _xb_decide(obs, player, st):
    farm = obs['farms'][player]
    crop = _XB_CFG['crop']
    owned = 'SE' in farm['unlocked_quadrants']
    if int(obs['market']['prices'].get(crop, 0)) < _XB_CFG['min_price']: return None
    shops = list(obs['town']['unlocked_shops'])
    nshops = sum(crop in _XB_SHOP_GOODS.get(s, ()) for s in shops)
    if nshops < _XB_CFG.get('min_shops', 0): return None
    if not owned:
        if not _XB_CFG.get('buy_land'): return None
        if set(farm['unlocked_quadrants']) != {'NW', 'NE', 'SW'}: return None
        for d in range(obs['step'] // 24, 30):
            for a in _xb_native_day(player, d):
                if any(o and o[0] == 'BUY_LAND' for o in a.get('market', [])): return None
    tiles = _xb_candidates(obs, player)[:int(_XB_CFG['n'])]
    if len(tiles) < _XB_CFG['min_tiles']: return None
    return dict(tiles=tiles, buy_land=not owned, nshops=nshops)


''')

span('def _xb_tile_tasks(obs, st, day):', 'def _xb_crew_size(obs, st, day, hour):', '''def _xb_tile_tasks(obs, st, day):
    """Per-tile task list for today: (tile, op) in priority order."""
    farm = obs['farms'][st['player']]
    crop = _XB_CFG['crop']; fy, iv, _ = _XB_CROP[crop]
    tasks = []
    for (x, y) in st['tiles']:
        t = farm['tiles'][y][x]
        if (x, y) in st['lost']: continue
        mine = isinstance(t, dict) and t.get('crop') == crop
        if not mine:
            if (x, y) in st['planted']:
                st['lost'].add((x, y)); _XB_REPORT['lost'] += 1; continue
            if day <= st['plant_last']:
                if isinstance(t, dict) and t.get('kind') == 'WEED': tasks.append(((x, y), 'DIG'))
                elif t is None: tasks.append(((x, y), 'PLANT'))
            continue
        st['planted'].add((x, y))
        age = day - int(t['planted_day'])
        units = int(t.get('yield_units', 0) or 0)
        done = int(t.get('max_lifespan_step', -1)) >= 0
        k = age + 1 - fy
        eve = k >= 0 and k % iv == 0 and k // iv + 1 <= 4 and day <= 28
        if units >= _XB_CFG['harvest_at'] or (done and units > 0) or (day >= 28 and units > 0) or (eve and units + 2 > 4):
            tasks.append(((x, y), 'HARVEST'))
        if not done and day < 29:
            if not t.get('watered_today') and (int(t.get('consecutive_unwatered', 0)) >= 1 or eve or age == 0):
                tasks.append(((x, y), 'WATER'))
            if _XB_CFG['fertilize'] and eve and int(t.get('fertilized_until_day', -1)) < day:
                tasks.append(((x, y), 'FERTILIZE'))
    return tasks


''')

rep("    tom = int(inv.get('TOMATO', 0))\n", "    crop = _XB_CFG['crop']\n    tom = int(inv.get(crop, 0))\n")
s = s.replace("return _xb_walk(pos, home) or ['PLACE', 'TOMATO', tom]", "return _xb_walk(pos, home) or _xb_place(st, crop, tom)")
rep("    seeds = int(private['seeds'].get('TOMATO', 0))", "    seeds = int(private['seeds'].get(crop, 0))")
rep("        return [op] if op != 'PLANT' else ['PLANT', 'TOMATO']", "        return [op] if op != 'PLANT' else ['PLANT', crop]")
rep("    if any(int(v) > 0 for k, v in inv.items() if k != 'FERTILIZER'):",
    "    if any(int(v) > 0 for k, v in inv.items() if k not in ('FERTILIZER', crop)):")
rep("def _xb_worker(obs, st, actor, role):", '''def _xb_place(st, crop, q):
    st['to_sell'] = st.get('to_sell', 0) + q
    return ['PLACE', crop, q]


def _xb_worker(obs, st, actor, role):''')
rep("            cost = len(dec['tiles']) * 50 + (4000 if dec['buy_land'] else 0)",
    "            cost = len(dec['tiles']) * _XB_CROP[_XB_CFG['crop']][2] + (4000 if dec['buy_land'] else 0)")
rep("                orders.append(['BUY_SEED', 'TOMATO', len(dec['tiles'])])",
    "                orders.append(['BUY_SEED', _XB_CFG['crop'], len(dec['tiles'])])")

span("    # --- sell tomatoes from the shed", "    if changed:\n        action = dict(action); action['market'] = market\n    return action", '''    # --- sell what the crew delivered; the chassis keeps its own stock of this crop --------------
    crop = _XB_CFG['crop']
    if hour == 0 and st.get('carry_day') != day:
        st['carry_day'] = day
        st['to_sell'] = st.get('to_sell', 0) + st.pop('carried', 0)
    if hour == 23:
        st['carried'] = sum(int((private['inventories'][a] if a < len(private['inventories']) else {}).get(crop, 0)) for a in st['crew'])
    q_all = min(int(st.get('to_sell', 0)), int(private['shed'].get(crop, 0)))
    if q_all > 0 and len(market) < 10:
        price = int(obs['market']['prices'].get(crop, 0))
        if price >= _XB_CFG['sell_min'] or day >= 28:
            q = q_all if day >= 28 else min(q_all, _XB_CFG['sell_lot'])
            market = [['SELL', crop, q]] + market; changed = True
            st['to_sell'] -= q
            _XB_REPORT['sold_units'] += q
''')
open(os.path.join(HERE, 'xb_layer.py'), 'w', encoding='utf-8').write(s)
print('written', len(s), 'TOMATO refs left:', s.count("'TOMATO'"))
