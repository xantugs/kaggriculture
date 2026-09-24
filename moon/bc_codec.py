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
