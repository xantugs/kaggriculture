"""Observation -> model features for the imitation planner. Pure Python; shared by extraction and the agent.

Tile features (per own tile, 100 tiles, row-major y*10+x):
  cat   : tile category index (CATS)
  num   : [age/16, yield/6, unwatered, fert_active, done, fed_today, unfed, cared, pending/3, fert_avail, watered]
  rcat  : rival tile category index
Global features: GLOBAL_NAMES (floats, roughly unit scale).
Labels (per tile, bitmask over LABELS) and day-level targets are produced by extract.py."""

CATS = ['EMPTY', 'LOCKED', 'WEED', 'WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'COOP', 'PASTURE', 'GOOSE', 'COW', 'SHEEP']
CAT_I = {c: i for i, c in enumerate(CATS)}
LABELS = ['WATER', 'HARVEST', 'FERTILIZE', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'DIG',
          'PLANT_WHEAT', 'PLANT_CARROT', 'PLANT_TOMATO', 'PLANT_STRAWBERRY', 'PLANT_MELON',
          'BUILD_COOP', 'BUILD_PASTURE', 'PLACE_GOOSE', 'PLACE_COW', 'PLACE_SHEEP']
LABEL_I = {l: i for i, l in enumerate(LABELS)}
PRODUCTS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']
BASE = {'WHEAT': 25, 'CARROT': 35, 'TOMATO': 60, 'STRAWBERRY': 120, 'MELON': 250, 'EGG': 50, 'MILK': 160, 'WOOL': 200, 'FERTILIZER': 100}
SHOPS = ['BAKERY', 'PIZZA_SHOP', 'BRUNCH_SPOT', 'YARN_STORE', 'ICE_CREAM_SHOP', 'PET_CAFE', 'SMOOTHIE_SHOP', 'FARMERS_MARKET']
ANIMALS = ['GOOSE', 'COW', 'SHEEP']
CROPS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON']
N_NUM = 11

GLOBAL_NAMES = (['day', 'money', 'rmoney', 'nquad', 'rnquad']
                + ['shed_' + p for p in PRODUCTS] + ['shed_' + a for a in ANIMALS] + ['seed_' + c for c in CROPS]
                + ['px_' + p for p in PRODUCTS] + ['inv_' + p for p in PRODUCTS]
                + ['shop_' + s for s in SHOPS] + ['nshops']
                + ['own_' + c for c in CATS] + ['riv_' + c for c in CATS])


def _g(d, k, default=None):
    if isinstance(d, dict):
        return d.get(k, default)
    return getattr(d, k, default)


def tile_cat(t):
    if t is None:
        return 0
    if t == 'LOCKED':
        return 1
    if isinstance(t, dict):
        if 'animal' in t:
            return CAT_I.get(t['animal'], 0)
        k = t.get('kind')
        if k == 'PLANT':
            return CAT_I.get(t.get('crop'), 0)
        if k == 'WEED':
            return 2
        if k == 'COOP':
            return 8
        if k == 'PASTURE':
            return 9
    return 0


def tile_num(t, day):
    if not isinstance(t, dict):
        return [0.0] * N_NUM
    if t.get('kind') == 'PLANT':
        age = day - int(t.get('planted_day', day))
        return [age / 16.0, t.get('yield_units', 0) / 6.0, float(t.get('consecutive_unwatered', 0)),
                1.0 if t.get('fertilized_until_day', -1) >= day else 0.0, 1.0 if t.get('max_lifespan_step', -1) >= 0 else 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 1.0 if t.get('watered_today') else 0.0]
    if 'animal' in t:
        age = day - int(t.get('placed_day', day))
        return [age / 16.0, t.get('yield_units', 0) / 6.0, 0.0, 0.0, 0.0,
                1.0 if t.get('fed_today') else 0.0, float(t.get('consecutive_unfed', 0)), 1.0 if t.get('cared_today') else 0.0,
                t.get('pending_care_bonus', 0) / 3.0, 1.0 if t.get('fertilizer_available') else 0.0, 0.0]
    return [0.0] * N_NUM


def features(obs, player=None):
    """Returns (cats[100], nums[100][N_NUM], rcats[100], glob[len(GLOBAL_NAMES)])."""
    p = int(_g(obs, 'player', 0) if player is None else player)
    farms = _g(obs, 'farms')
    me, rv = farms[p], farms[1 - p]
    step = int(_g(obs, 'step', 0)); day = step // 24
    cats, nums, rcats = [], [], []
    own_c = [0] * len(CATS); riv_c = [0] * len(CATS)
    for y in range(10):
        for x in range(10):
            t = me['tiles'][y][x]; r = rv['tiles'][y][x]
            c = tile_cat(t); rc = tile_cat(r)
            cats.append(c); rcats.append(rc); nums.append(tile_num(t, day))
            own_c[c] += 1; riv_c[rc] += 1
    priv = _g(obs, 'private') or {}
    shed = _g(priv, 'shed', {}) or {}
    seeds = _g(priv, 'seeds', {}) or {}
    mk = _g(obs, 'market') or {}
    prices = _g(mk, 'prices', {}) or {}; inv = _g(mk, 'inventory', {}) or {}
    shops = list(_g(_g(obs, 'town') or {}, 'unlocked_shops', []) or [])
    g = [day / 30.0, float(me['money']) / 1e5, float(rv['money']) / 1e5,
         len(me.get('unlocked_quadrants', [])) / 4.0, len(rv.get('unlocked_quadrants', [])) / 4.0]
    g += [float(shed.get(k, 0)) / 50.0 for k in PRODUCTS] + [float(shed.get(a, 0)) for a in ANIMALS]
    g += [float(seeds.get(c, 0)) / 10.0 for c in CROPS]
    g += [float(prices.get(k, BASE[k])) / BASE[k] for k in PRODUCTS]
    g += [(float(inv.get(k, 10000)) - 10000.0) / 200.0 for k in PRODUCTS]
    g += [float(shops.count(s)) for s in SHOPS] + [len(shops) / 8.0]
    g += [v / 25.0 for v in own_c] + [v / 25.0 for v in riv_c]
    return cats, nums, rcats, g


def tile_inputs(c, n, r, G):
    """Per-tile input rows (100 x D) built from extracted/observed features; identical at play time."""
    NC = len(CATS)
    rows = []
    for i in range(100):
        x, y = i % 10, i // 10
        v = [0.0] * NC; v[c[i]] = 1.0
        v += list(n[i])
        rv = [0.0] * NC; rv[r[i]] = 1.0
        nb = [0.0] * NC
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                xx, yy = x + dx, y + dy
                if (dx or dy) and 0 <= xx < 10 and 0 <= yy < 10:
                    nb[c[yy * 10 + xx]] += 1.0 / 8.0
        xo = [0.0] * 10; xo[x] = 1.0
        yo = [0.0] * 10; yo[y] = 1.0
        rows.append(v + rv + nb + xo + yo)
    return rows   # the global vector G is appended by the model separately
