

# =====================================================================================
# BC: behaviour-cloned policy of top teams (per-unit commands + market orders), trained on Kaggle.
# Model code runs in its own namespace. Without numpy the chassis plays the whole game unchanged.
# =====================================================================================
import json as _bc_json
import zlib as _bc_zlib
import base64 as _bc_b64
import io as _bc_io
_BC_SRC = __BC_SRC__
_BC_W = __BC_W__
_BC_START = __BC_START__
_BC_REPORT = dict(bc_steps=0, bc_errors=0, bc_masked=0, bc_numpy=0, bc_last_error='')
_BC = {}


def _bc_load():
    if 'ns' in _BC:
        return _BC['ns']
    try:
        import numpy as np
        ns = {}
        exec(compile(_BC_SRC, 'bc_model', 'exec'), ns)
        raw = _bc_zlib.decompress(_bc_b64.b85decode(_BC_W))
        z = np.load(_bc_io.BytesIO(raw))
        ns['W'] = {k: z[k].astype(np.float32) for k in z.files}
        ns['np'] = np
        _BC['ns'] = ns
        _BC_REPORT['bc_numpy'] = 1
    except Exception as e:
        _BC['ns'] = None
        _BC_REPORT['bc_last_error'] = repr(e)[:200]
    return _BC['ns']


_BC_ACCESS = ((4, 4), (5, 4), (4, 5), (5, 5))
_BC_MOVES = {'NORTH': (0, -1), 'SOUTH': (0, 1), 'EAST': (1, 0), 'WEST': (-1, 0)}
_BC_ANIM_ST = {'GOOSE': 'COOP', 'COW': 'PASTURE', 'SHEEP': 'PASTURE'}


def _bc_legal(a, pos, tile, inv, shed_left, seeds_left, locked):
    x, y = pos
    if a in _BC_MOVES:
        dx, dy = _BC_MOVES[a]
        return 0 <= x + dx < 10 and 0 <= y + dy < 10
    if a == 'PASS':
        return True
    is_plant = isinstance(tile, dict) and tile.get('kind') == 'PLANT'
    is_anim = isinstance(tile, dict) and 'animal' in tile
    at_shed = (x, y) in _BC_ACCESS
    if a.startswith('PICKUP_'):
        return at_shed and shed_left.get(a[7:], 0) > 0
    if a == 'DROP':
        return at_shed and any(v > 0 for v in inv.values())
    if a.startswith('DEPOSIT_'):
        return at_shed and inv.get(a[8:], 0) > 0
    if locked:
        return False
    if a == 'WATER':
        return is_plant and not tile.get('watered_today')
    if a == 'HARVEST':
        return isinstance(tile, dict) and tile.get('yield_units', 0) > 0 and (is_anim or is_plant)
    if a == 'FERTILIZE':
        return is_plant and inv.get('FERTILIZER', 0) > 0
    if a == 'FEED':
        return is_anim and not tile.get('fed_today') and inv.get('WHEAT', 0) > 0
    if a == 'CARE':
        return is_anim and not tile.get('cared_today')
    if a == 'COLLECT_FERTILIZER':
        return is_anim and tile.get('fertilizer_available')
    if a == 'DIG':
        return tile is not None and not is_anim
    if a.startswith('PLANT_'):
        return tile is None and seeds_left.get(a[6:], 0) > 0
    if a in ('BUILD_COOP', 'BUILD_PASTURE'):
        return tile is None
    if a.startswith('PLACE_'):
        an = a[6:]
        return isinstance(tile, dict) and tile.get('kind') == _BC_ANIM_ST[an] and 'animal' not in tile and inv.get(an, 0) > 0
    return False


def _bc_act(obs, cfg):
    ns = _bc_load()
    if ns is None:
        return None
    np = ns['np']
    p = int(obs['player'])
    farm = obs['farms'][p]
    priv = obs.get('private') or {}
    grid, glob, uvec = ns['encode'](obs, p, ns['features'])
    grid, glob, uvs = ns['quantize'](grid, glob, [u[1] for u in uvec])
    ua, uq, mk = ns['forward'](ns['W'], grid, glob, uvs, [u[0] for u in uvec])
    UA = ns['UA']
    shed_left = dict(priv.get('shed') or {})
    seeds_left = dict(priv.get('seeds') or {})
    invs = priv.get('inventories') or []
    cmds = []
    for k, ((x, y), _) in enumerate(uvec):
        tile = farm['tiles'][y][x]
        locked = tile == 'LOCKED'
        inv = invs[k] if k < len(invs) else {}
        chosen = UA.index('PASS')
        for j in np.argsort(-ua[k]):
            if _bc_legal(UA[int(j)], (x, y), None if locked else tile, inv, shed_left, seeds_left, locked):
                chosen = int(j)
                break
            _BC_REPORT['bc_masked'] += 1
        a = UA[chosen]
        q = int(np.argmax(uq[k]))
        if a.startswith('PICKUP_'):
            item = a[7:]
            q = min(q + 1, int(shed_left.get(item, 0))) - 1
            shed_left[item] = shed_left.get(item, 0) - (q + 1)
        if a.startswith('PLANT_'):
            seeds_left[a[6:]] = seeds_left.get(a[6:], 0) - 1
        cmds.append(ns['decode_unit'](chosen, max(0, q), inv))
    lab = {h: int(np.argmax(mk[h])) for h in ns['MARKET_HEADS']}
    market = ns['decode_market'](lab)
    _BC_REPORT['bc_steps'] += 1
    return {'farmer': cmds[0], 'hands': cmds[1:], 'market': market}


try:
    _bc_load()   # decode weights at import, not inside a timed turn
except Exception:
    pass
_BC_PARENT = globals().pop('kaggle_submission_agent')
globals().pop('agent', None)


def agent(observation, configuration=None):
    step = int(observation['step'])
    if step >= _BC_START and _bc_load() is not None:
        try:
            import time as _bc_time
            _t = _bc_time.perf_counter()
            a = _bc_act(observation, configuration)
            _BC_REPORT['bc_time'] = _BC_REPORT.get('bc_time', 0.0) + (_bc_time.perf_counter() - _t)
            if a is not None:
                return a
        except Exception as e:
            _BC_REPORT['bc_errors'] += 1; _BC_REPORT['bc_last_error'] = repr(e)[:200]
            farm = observation['farms'][int(observation['player'])]
            return {'farmer': ['PASS'], 'hands': [['PASS'] for _ in farm['hands']], 'market': []}
    return _BC_PARENT(observation, configuration)


agent.telemetry = _BC_REPORT
agent = globals().pop('agent')
kaggle_submission_agent = agent
