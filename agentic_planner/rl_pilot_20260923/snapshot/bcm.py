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


"""Behaviour-cloning action codec v2 (pure Python). Encodes a recorded teacher action into class labels and decodes
class labels back into an executable action. Designed so that perfect labels reproduce the teacher's game exactly:
exact pickup quantities, deposit-by-item, exact market quantities, and the teachers' market order
(sales first, then hires, land, animals, seeds, product purchases). Verified by bc_gate.py."""

UA = ['NORTH', 'SOUTH', 'EAST', 'WEST', 'PASS', 'WATER', 'HARVEST', 'FERTILIZE', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'DIG',
      'PLANT_WHEAT', 'PLANT_CARROT', 'PLANT_TOMATO', 'PLANT_STRAWBERRY', 'PLANT_MELON', 'BUILD_COOP', 'BUILD_PASTURE',
      'PLACE_GOOSE', 'PLACE_COW', 'PLACE_SHEEP',
      'PICKUP_WHEAT', 'PICKUP_FERTILIZER', 'PICKUP_GOOSE', 'PICKUP_COW', 'PICKUP_SHEEP',
      'DROP'] + ['DEPOSIT_' + p for p in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER')]
UA_I = {a: i for i, a in enumerate(UA)}
NQ = 20                        # pickup quantity classes: q in 1..20 -> class q-1 (20 = 20 or more)
PRODUCTS9 = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']
ANIMALS3 = ['GOOSE', 'COW', 'SHEEP']
CROPS5 = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON']
SELL_MAX = 31                  # sell classes 0..30 exact, 31 -> "big standing order" (value SELL_BIG)
SELL_BIG = 60
MARKET_HEADS = (['hires', 'land'] + ['anim_' + a for a in ANIMALS3] + ['seed_' + c for c in CROPS5]
                + ['buy_WHEAT', 'buy_FERTILIZER'] + ['sell_' + p for p in PRODUCTS9])
MARKET_SIZES = ([11, 2] + [5] * 3 + [21] * 5 + [41] * 2 + [SELL_MAX + 1] * 9)


def unit_label(a):
    """Recorded unit command -> (class, qty_class)."""
    if not isinstance(a, list) or not a:
        return UA_I['PASS'], 0
    op = a[0]
    if op == 'PLANT' and len(a) > 1 and ('PLANT_' + str(a[1])) in UA_I:
        return UA_I['PLANT_' + str(a[1])], 0
    if op == 'PICKUP' and len(a) > 1 and ('PICKUP_' + str(a[1])) in UA_I:
        n = int(a[2]) if len(a) > 2 else 1
        return UA_I['PICKUP_' + str(a[1])], max(0, min(NQ, n) - 1)
    if op == 'PLACE' and len(a) > 1:
        if a[1] in ANIMALS3:
            return UA_I['PLACE_' + a[1]], 0
        if ('DEPOSIT_' + str(a[1])) in UA_I:
            return UA_I['DEPOSIT_' + str(a[1])], 0
        return UA_I['DROP'], 0
    if op in UA_I:
        return UA_I[op], 0
    return UA_I['PASS'], 0


def decode_unit(cls, qcls, inv):
    """(class, qty_class, carried inventory) -> engine command."""
    a = UA[cls]
    if a.startswith('PLANT_'):
        return ['PLANT', a[6:]]
    if a.startswith('PICKUP_'):
        return ['PICKUP', a[7:], int(qcls) + 1]
    if a.startswith('PLACE_'):
        return ['PLACE', a[6:]]
    if a.startswith('DEPOSIT_'):
        item = a[8:]
        return ['PLACE', item, max(1, int(inv.get(item, 0)))]
    return [a]


def market_labels(orders):
    """Recorded market orders -> {head: class} with exact quantities."""
    out = {h: 0 for h in MARKET_HEADS}
    for o in orders or []:
        if not o:
            continue
        op = o[0]
        n = int(o[2]) if len(o) > 2 and isinstance(o[2], (int, float)) else 1
        if op == 'HIRE':
            out['hires'] = min(10, out['hires'] + 1)
        elif op == 'BUY_LAND':
            out['land'] = 1
        elif op == 'BUY_ANIMAL' and len(o) > 1 and o[1] in ANIMALS3:
            out['anim_' + o[1]] = min(4, out['anim_' + o[1]] + n)
        elif op == 'BUY_SEED' and len(o) > 1 and o[1] in CROPS5:
            out['seed_' + o[1]] = min(20, out['seed_' + o[1]] + n)
        elif op == 'BUY_PRODUCT' and len(o) > 1 and o[1] in ('WHEAT', 'FERTILIZER'):
            out['buy_' + o[1]] = min(40, out['buy_' + o[1]] + n)
        elif op == 'SELL' and len(o) > 1 and o[1] in PRODUCTS9:
            cur = out['sell_' + o[1]]
            tot = (SELL_BIG if cur == SELL_MAX else cur) + n
            out['sell_' + o[1]] = SELL_MAX if tot > 30 else tot
    return out


def decode_market(lab):
    """{head: class} -> ordered market orders (sales first, as the teachers do), at most 10."""
    orders = []
    for p in PRODUCTS9:
        c = int(lab.get('sell_' + p, 0))
        if c > 0:
            orders.append(['SELL', p, SELL_BIG if c == SELL_MAX else c])
    orders += [['HIRE']] * int(lab.get('hires', 0))
    if int(lab.get('land', 0)) == 1:
        orders.append(['BUY_LAND'])
    for an in ANIMALS3:
        n = int(lab.get('anim_' + an, 0))
        if n > 0:
            orders.append(['BUY_ANIMAL', an, n])
    for c in CROPS5:
        n = int(lab.get('seed_' + c, 0))
        if n > 0:
            orders.append(['BUY_SEED', c, n])
    for it in ('WHEAT', 'FERTILIZER'):
        n = int(lab.get('buy_' + it, 0))
        if n > 0:
            orders.append(['BUY_PRODUCT', it, n])
    return orders[:10]


def roundtrip(action, invs):
    """Teacher action -> labels -> decoded action (the perfect-label reconstruction)."""
    cmds = [action.get('farmer')] + list(action.get('hands') or [])
    out = []
    for k, c in enumerate(cmds):
        cls, q = unit_label(c)
        out.append(decode_unit(cls, q, invs[k] if k < len(invs) else {}))
    return {'farmer': out[0], 'hands': out[1:], 'market': decode_market(market_labels(action.get('market') or []))}


"""Behaviour cloning v2: observation encoding and numpy forward pass. Relies on bc_codec (UA, NQ, MARKET_HEADS,
MARKET_SIZES) being defined in the same namespace (the builders concatenate bc_codec.py before this file).
Grid channels (C=38 per tile): own category one-hot (13), own numeric (11), rival category one-hot (13), own-unit count.
Global vector: feat.features() globals + hour one-hot + hires/hands/step + carried totals (12).
Unit vector: x one-hot, y one-hot, unit index one-hot (16), carried items (12)."""
import numpy as np

ITEMS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER', 'GOOSE', 'COW', 'SHEEP']
C_GRID = 38
N_UNIT = 10 + 10 + 16 + 12


def encode(obs, p, features):
    """-> grid [C,10,10] float32, glob [G] float32, and the per-unit list [(pos, unit_vec)]."""
    cats, nums, rcats, G = features(obs, p)
    grid = np.zeros((C_GRID, 100), np.float32)
    idx = np.arange(100)
    grid[np.asarray(cats), idx] = 1.0
    grid[13:24, :] = np.asarray(nums, np.float32).T
    grid[24 + np.asarray(rcats), idx] = 1.0
    farm = obs['farms'][p]
    units = [tuple(farm['farmer'])] + [tuple(h) for h in farm['hands']]
    for (x, y) in units:
        grid[37, y * 10 + x] += 1.0 / 3.0
    hour = int(obs['step']) % 24
    hv = np.zeros(24, np.float32); hv[hour] = 1.0
    invs = (obs.get('private') or {}).get('inventories') or []
    carried = np.zeros(12, np.float32)
    uvec = []
    for k, (x, y) in enumerate(units):
        v = np.zeros(N_UNIT, np.float32)
        v[x] = 1.0; v[10 + y] = 1.0; v[20 + min(k, 15)] = 1.0
        inv = invs[k] if k < len(invs) else {}
        for j, it in enumerate(ITEMS):
            c = float(inv.get(it, 0))
            v[36 + j] = c / 10.0
            carried[j] += c
        uvec.append(((x, y), v))
    glob = np.concatenate([np.asarray(G, np.float32), hv,
                           np.asarray([farm.get('hires_today', 0) / 10.0, len(farm['hands']) / 12.0, int(obs['step']) / 720.0], np.float32),
                           carried / 20.0])
    return grid.reshape(C_GRID, 10, 10), glob, uvec


def quantize(grid, glob, uvecs):
    """Apply the training-store rounding (uint8 / float16) so play-time inputs match what the model was fit on."""
    g = grid.reshape(C_GRID, 100).copy()
    g[13:24] = np.clip(g[13:24] * 50.0, 0, 255).astype(np.uint8).astype(np.float32) / 50.0
    g[37] = np.clip(g[37] * 3.0, 0, 255).astype(np.uint8).astype(np.float32) / 3.0
    uq = []
    for u in uvecs:
        u = u.copy(); u[36:48] = np.clip(u[36:48] * 10.0, 0, 255).astype(np.uint8).astype(np.float32) / 10.0; uq.append(u)
    return g.reshape(C_GRID, 10, 10), glob.astype(np.float16).astype(np.float32), uq


def conv3(x, w, b):
    """x [Cin,10,10], w [Cout,Cin,3,3] -> [Cout,10,10] (padding 1) via im2col."""
    cin = x.shape[0]
    xp = np.zeros((cin, 12, 12), np.float32); xp[:, 1:11, 1:11] = x
    cols = np.empty((9, cin, 100), np.float32)
    k = 0
    for dy in range(3):
        for dx in range(3):
            cols[k] = xp[:, dy:dy + 10, dx:dx + 10].reshape(cin, 100)
            k += 1
    wm = w.transpose(0, 2, 3, 1).reshape(w.shape[0], 9 * cin)
    return (wm @ cols.reshape(9 * cin, 100) + b[:, None]).reshape(w.shape[0], 10, 10)


def forward(W, grid, glob, uvecs, upos, n_conv=4):
    """Returns (unit logits [U,A], qty logits [U,NQ], market logits dict)."""
    h = grid
    for i in range(n_conv):
        h = np.maximum(0.0, conv3(h, W['c%d.weight' % i], W['c%d.bias' % i]))
    gv = np.maximum(0.0, W['g.weight'] @ glob + W['g.bias'])
    pooled = h.reshape(h.shape[0], 100).mean(1)
    hp = np.zeros((h.shape[0], 12, 12), np.float32); hp[:, 1:11, 1:11] = h
    U = []
    for (x, y), uv in zip(upos, uvecs):
        loc = [hp[:, y + 1, x + 1], hp[:, y, x + 1], hp[:, y + 2, x + 1], hp[:, y + 1, x + 2], hp[:, y + 1, x]]
        U.append(np.concatenate(loc + [pooled, gv, uv]))
    U = np.asarray(U, np.float32)
    z = np.maximum(0.0, U @ W['u1.weight'].T + W['u1.bias'])
    ua = z @ W['ua.weight'].T + W['ua.bias']
    uq = z @ W['uq.weight'].T + W['uq.bias']
    m = np.maximum(0.0, W['m1.weight'] @ np.concatenate([pooled, gv]) + W['m1.bias'])
    mk = {name: W['mh_%s.weight' % name] @ m + W['mh_%s.bias' % name] for name in MARKET_HEADS}
    return ua, uq, mk
