# Kaggriculture behaviour cloning of top teams: per-unit commands and market orders.
import subprocess, sys, os, json
import importlib.metadata as _md
try:
    _v = _md.version('kaggle-environments')
except Exception:
    _v = None
print('preinstalled kaggle-environments', _v, flush=True)
if _v != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
TEACHERS = ['DSM', 'Vadim Vasilenko']
MAX_GAMES = 1200
EPOCHS = 10
HIDDEN = 64
WINS_ONLY = 0

# ---- feat ----


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

# ---- bc core ----

import numpy as np

UA = ['NORTH', 'SOUTH', 'EAST', 'WEST', 'PASS', 'WATER', 'HARVEST', 'FERTILIZE', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'DIG',
      'PLANT_WHEAT', 'PLANT_CARROT', 'PLANT_TOMATO', 'PLANT_STRAWBERRY', 'PLANT_MELON', 'BUILD_COOP', 'BUILD_PASTURE',
      'PLACE_GOOSE', 'PLACE_COW', 'PLACE_SHEEP', 'PICKUP_WHEAT', 'PICKUP_FERTILIZER', 'PICKUP_GOOSE', 'PICKUP_COW', 'PICKUP_SHEEP',
      'DROP', 'DEPOSIT']
UA_I = {a: i for i, a in enumerate(UA)}
QTY = [1, 2, 4, 8, 12, 20]                    # pickup quantity bins (representative values)
ITEMS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER', 'GOOSE', 'COW', 'SHEEP']
SELL_BINS = [0.0, 0.25, 0.5, 0.75, 1.0]      # fraction of shed stock sold this step (class k: <= edge)
BUY_BINS = [0, 2, 5, 10, 20, 40, 10 ** 6]    # units bought (class k: <= edge)
SEED_BINS = [0, 1, 2, 5, 10, 10 ** 6]
C_GRID = 38
N_UNIT = 10 + 10 + 16 + 12


def qty_bin(n):
    for k, v in enumerate([1, 2, 4, 8, 16]):
        if n <= v:
            return k
    return 5


def bin_of(n, edges):
    for k, e in enumerate(edges):
        if n <= e:
            return k
    return len(edges) - 1


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
    glob = np.concatenate([np.asarray(G, np.float32), hv,
                           np.asarray([farm.get('hires_today', 0) / 10.0, len(farm['hands']) / 12.0, int(obs['step']) / 720.0], np.float32)])
    invs = (obs.get('private') or {}).get('inventories') or []
    uvec = []
    for k, (x, y) in enumerate(units):
        v = np.zeros(N_UNIT, np.float32)
        v[x] = 1.0; v[10 + y] = 1.0; v[20 + min(k, 15)] = 1.0
        inv = invs[k] if k < len(invs) else {}
        for j, it in enumerate(ITEMS):
            v[36 + j] = float(inv.get(it, 0)) / 10.0
        uvec.append(((x, y), v))
    return grid.reshape(C_GRID, 10, 10), glob, uvec


def unit_label(a):
    """Recorded unit command -> (class, qty_bin)."""
    if not isinstance(a, list) or not a:
        return UA_I['PASS'], 0
    op = a[0]
    if op in UA_I and op not in ('PLACE',):
        return UA_I[op], 0
    if op == 'PLANT' and len(a) > 1 and 'PLANT_' + str(a[1]) in UA_I:
        return UA_I['PLANT_' + str(a[1])], 0
    if op == 'PICKUP' and len(a) > 1 and 'PICKUP_' + str(a[1]) in UA_I:
        n = int(a[2]) if len(a) > 2 else 1
        return UA_I['PICKUP_' + str(a[1])], qty_bin(n)
    if op == 'PLACE' and len(a) > 1:
        if a[1] in ('GOOSE', 'COW', 'SHEEP'):
            return UA_I['PLACE_' + a[1]], 0
        return UA_I['DEPOSIT'], 0
    return UA_I['PASS'], 0


def market_labels(orders, shed):
    """Recorded market orders -> dict of class targets."""
    hires = land = 0
    anim = {'GOOSE': 0, 'COW': 0, 'SHEEP': 0}
    seed = {c: 0 for c in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON')}
    buy = {'WHEAT': 0, 'FERTILIZER': 0}
    sell = {p: 0 for p in ITEMS[:9]}
    for o in orders or []:
        if not o:
            continue
        op = o[0]
        n = int(o[2]) if len(o) > 2 and isinstance(o[2], (int, float)) else 1
        if op == 'HIRE': hires += 1
        elif op == 'BUY_LAND': land = 1
        elif op == 'BUY_ANIMAL' and len(o) > 1 and o[1] in anim: anim[o[1]] += n
        elif op == 'BUY_SEED' and len(o) > 1 and o[1] in seed: seed[o[1]] += n
        elif op == 'BUY_PRODUCT' and len(o) > 1 and o[1] in buy: buy[o[1]] += n
        elif op == 'SELL' and len(o) > 1 and o[1] in sell: sell[o[1]] += n
    out = dict(hires=min(hires, 10), land=land)
    for a in anim: out['anim_' + a] = min(anim[a], 2)
    for c in seed: out['seed_' + c] = bin_of(seed[c], SEED_BINS)
    for p in buy: out['buy_' + p] = bin_of(buy[p], BUY_BINS)
    for p in sell:
        have = float(shed.get(p, 0))
        f = min(1.0, sell[p] / have) if have > 0 else (1.0 if sell[p] > 0 else 0.0)
        out['sell_' + p] = 0 if sell[p] <= 0 else max(1, bin_of(f, SELL_BINS))
    return out


MARKET_HEADS = (['hires', 'land'] + ['anim_' + a for a in ('GOOSE', 'COW', 'SHEEP')]
                + ['seed_' + c for c in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON')]
                + ['buy_WHEAT', 'buy_FERTILIZER'] + ['sell_' + p for p in ITEMS[:9]])
MARKET_SIZES = ([11, 2] + [3] * 3 + [len(SEED_BINS)] * 5 + [len(BUY_BINS)] * 2 + [len(SELL_BINS)] * 9)


# ------------------------------------------------------------------ numpy forward pass (play time)
def conv3(x, w, b):
    """x [Cin,10,10], w [Cout,Cin,3,3] -> [Cout,10,10] (padding 1) via im2col."""
    cin = x.shape[0]
    xp = np.zeros((cin, 12, 12), np.float32); xp[:, 1:11, 1:11] = x
    cols = np.empty((cin * 9, 100), np.float32)
    k = 0
    for dy in range(3):
        for dx in range(3):
            cols[k * cin:(k + 1) * cin] = xp[:, dy:dy + 10, dx:dx + 10].reshape(cin, 100)
            k += 1
    wm = w.transpose(0, 2, 3, 1).reshape(w.shape[0], 9 * cin)   # [Cout, (dy,dx,cin)]
    return (wm @ cols + b[:, None]).reshape(w.shape[0], 10, 10)


def forward(W, grid, glob, uvecs, upos):
    """Returns (unit logits [U,A], qty logits [U,6], market logits dict)."""
    h = grid
    for i in range(4):
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
    mk = {}
    for name in MARKET_HEADS:
        mk[name] = W['mh_%s.weight' % name] @ m + W['mh_%s.bias' % name]
    return ua, uq, mk

# ---- lean runner ----

import sys, os, time, json, contextlib, io, warnings, copy
warnings.filterwarnings("ignore")
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    from kaggle_environments.utils import Struct, structify

_CFG_DEFAULTS = {}
for k, v in K.specification["configuration"].items():
    if isinstance(v, dict) and "default" in v:
        _CFG_DEFAULTS[k] = v["default"]
    elif not isinstance(v, dict):
        _CFG_DEFAULTS[k] = v
_CFG_DEFAULTS.setdefault("episodeSteps", 720)
_CFG_DEFAULTS.setdefault("actTimeout", 1)
_CFG_DEFAULTS.setdefault("runTimeout", 1200)

class _Env:
    def __init__(self, seed, overrides=None):
        cfg = dict(_CFG_DEFAULTS)
        if overrides: cfg.update(overrides)
        cfg["seed"] = seed
        self.configuration = Struct(**cfg)
        self.info = {}
        self.done = False

_SRC = {}
def load(path):
    if path not in _SRC:
        raw = open(path, encoding="utf-8").read()
        _SRC[path] = compile(raw, path, "exec")
    code = _SRC[path]
    g = {"__name__": "agent_module_%d" % len(_SRC), "__file__": path}
    d = os.path.dirname(os.path.abspath(path))
    sys.path.append(d)
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(code, g)
    finally:
        sys.path.pop()
    return [v for v in g.values() if callable(v)][-1]

def _hook(d):
    return Struct(**d)

def _clone(o):
    # structify-equivalent deep clone via JSON (agents on Kaggle receive JSON-decoded Structs)
    return json.loads(json.dumps(o), object_hook=_hook)

SHARED = ("farms", "market", "town", "day", "hour", "step")

def play(pa, pb, seed, record=False, cfg_overrides=None, agent_objs=None, max_steps=None):
    """pa plays seat 0, pb seat 1. Returns dict with rewards, statuses, timing."""
    agents = agent_objs if agent_objs is not None else [load(pa), load(pb)]
    env = _Env(seed, cfg_overrides)
    cfgs = [_clone(dict(env.configuration)), _clone(dict(env.configuration))]
    state = [Struct(observation=Struct(step=0, remainingOverageTime=60, player=i), action=None,
                    reward=0, status="ACTIVE", info=Struct()) for i in range(2)]
    with contextlib.redirect_stdout(io.StringIO()):
        K.interpreter(state, env)
    # after reset, kaggle sets cfg seed None; agents never see it
    for c in cfgs: c["seed"] = None
    tmax = [0.0, 0.0]; tsum = [0.0, 0.0]; over = [0.0, 0.0]
    errors = [None, None]
    rec = [] if record else None
    step_counter = 0
    while True:
        obs0 = state[0].observation
        actions = []
        for i in range(2):
            if state[i].status != "ACTIVE":
                actions.append(None); continue
            o = {k: obs0[k] for k in SHARED if k in obs0}
            oi = state[i].observation
            o["player"] = oi["player"]; o["private"] = oi["private"]
            o["remainingOverageTime"] = oi.get("remainingOverageTime", 60)
            ob = _clone(o)
            t = time.perf_counter()
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    a = agents[i](ob, cfgs[i])
                a = json.loads(json.dumps(a))
            except Exception as e:
                a = e
            dt = time.perf_counter() - t
            tsum[i] += dt; tmax[i] = max(tmax[i], dt); over[i] += max(0.0, dt - 1.0)
            actions.append(a)
        if rec is not None:
            rec.append(actions)
        for i in range(2):
            a = actions[i]
            state[i]["action"] = None
            if state[i].status != "ACTIVE":
                continue
            if isinstance(a, BaseException):
                state[i].status = "ERROR"; errors[i] = repr(a)[:300]
            elif not isinstance(a, dict):
                state[i].status = "INVALID"; errors[i] = "non-dict action %r" % (type(a),)
            else:
                state[i]["action"] = structify(a)
                state[i].action = state[i]["action"]
        # mirror framework: interpreter sees structified state
        with contextlib.redirect_stdout(io.StringIO()):
            K.interpreter(state, env)
        step_counter += 1
        state[0].observation.step = step_counter
        for s in state:
            if s.status in ("ERROR", "INVALID", "TIMEOUT"):
                s.reward = None
        if state[0].observation.step >= env.configuration.episodeSteps - 1:
            for s in state:
                if s.status in ("ACTIVE", "INACTIVE"):
                    s.status = "DONE"
        if all(s.status != "ACTIVE" for s in state):
            break
        if max_steps is not None and step_counter >= max_steps:
            break
    out = {"seed": seed, "r": [state[0].reward, state[1].reward], "st": [state[0].status, state[1].status],
           "tmax": [round(x, 4) for x in tmax], "tsum": [round(x, 3) for x in tsum], "over": [round(x, 3) for x in over],
           "err": errors, "steps": step_counter}
    out["shops"] = list(state[0].observation.town.get("unlocked_shops", []))
    if record:
        out["actions"] = rec
        out["final_obs"] = state[0].observation
    return out



# ===================================== behaviour cloning driver =====================================
import glob, time, random, re


def header_teams(path):
    with open(path, 'rb') as fh:
        head = fh.read(200000).decode('utf-8', 'ignore')
    m = re.search(r'"TeamNames"\s*:\s*\[([^\]]*)\]', head)
    if not m:
        return None
    return json.loads('[' + m.group(1) + ']')


def extract_teacher(path):
    """Replay one game; for each teacher seat return compact per-step arrays."""
    import numpy as np
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    try:
        rep = json.load(open(path, encoding='utf-8'))
        names = (rep.get('info') or {}).get('TeamNames') or []
        seats = [i for i, n in enumerate(names) if n in TEACHERS]
        if not seats:
            return []
        acts = [[(x.get('action') if isinstance(x, dict) and isinstance(x.get('action'), dict) else None) for x in s]
                for s in rep.get('steps') or []]
        seed = (rep.get('info') or {}).get('seed')
        rew = rep.get('rewards')
        store = {p: dict(cats=[], rcats=[], nums=[], ucnt=[], glob=[], mk=[], u_step=[], u_x=[], u_y=[], u_k=[], u_inv=[], u_a=[], u_q=[])
                 for p in seats}

        def tape(p):
            def f(obs, cfg=None):
                t = obs['step']
                a = acts[t + 1][p] if t + 1 < len(acts) else None
                a = a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
                if p in store:
                    s = store[p]
                    grid, g, uvec = encode(obs, p, features)
                    gr = grid.reshape(C_GRID, 100)
                    s['cats'].append(np.argmax(gr[0:13], 0).astype(np.uint8))
                    s['rcats'].append(np.argmax(gr[24:37], 0).astype(np.uint8))
                    s['nums'].append(np.clip(gr[13:24] * 50.0, 0, 255).astype(np.uint8))
                    s['ucnt'].append(np.clip(gr[37] * 3.0, 0, 255).astype(np.uint8))
                    s['glob'].append(g.astype(np.float16))
                    shed = (obs.get('private') or {}).get('shed') or {}
                    ml = market_labels(a.get('market') or [], shed)
                    s['mk'].append(np.asarray([ml[h] for h in MARKET_HEADS], np.uint8))
                    cmds = [a.get('farmer')] + list(a.get('hands') or [])
                    si = len(s['cats']) - 1
                    for k, ((x, y), uv) in enumerate(uvec):
                        c, q = unit_label(cmds[k] if k < len(cmds) else ['PASS'])
                        s['u_step'].append(si); s['u_x'].append(x); s['u_y'].append(y); s['u_k'].append(min(k, 15))
                        s['u_inv'].append(np.clip(uv[36:48] * 10.0, 0, 255).astype(np.uint8)); s['u_a'].append(c); s['u_q'].append(q)
                return a
            return f
        r = play(None, None, seed, agent_objs=[tape(0), tape(1)])
        if [int(v) for v in r['r']] != [int(v) for v in rew]:
            return ['ERR not reproduced']
        out = []
        for p, s in store.items():
            won = int(rew[p] > rew[1 - p])
            out.append(dict(team=names[p], won=won, margin=float(rew[p] - rew[1 - p]),
                            cats=np.stack(s['cats']), rcats=np.stack(s['rcats']), nums=np.stack(s['nums']), ucnt=np.stack(s['ucnt']),
                            glob=np.stack(s['glob']), mk=np.stack(s['mk']),
                            u_step=np.asarray(s['u_step'], np.int32), u_x=np.asarray(s['u_x'], np.uint8), u_y=np.asarray(s['u_y'], np.uint8),
                            u_k=np.asarray(s['u_k'], np.uint8), u_inv=np.stack(s['u_inv']), u_a=np.asarray(s['u_a'], np.uint8),
                            u_q=np.asarray(s['u_q'], np.uint8)))
        return out
    except Exception:
        import traceback
        return ['ERR ' + traceback.format_exc()[-500:]]


def main():
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    files = sorted(glob.glob('/kaggle/input/**/*.json', recursive=True))
    files = [f for f in files if os.path.basename(f)[:-5].isdigit()]
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        heads = list(ex.map(header_teams, files, chunksize=32))
    tf = [f for f, h in zip(files, heads) if h and any(n in TEACHERS for n in h)]
    print('replays', len(files), 'with teachers', len(tf), round(time.time() - t0), 's', flush=True)
    random.seed(0); random.shuffle(tf); tf = tf[:MAX_GAMES]
    games = []; errs = 0
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        for k, res in enumerate(ex.map(extract_teacher, tf, chunksize=2)):
            for g in res:
                if isinstance(g, str):
                    errs += 1
                    if errs <= 3: print(g, flush=True)
                elif g['won'] or not WINS_ONLY:
                    games.append(g)
            if k % 50 == 0:
                print('extracted', k, 'teacher seats', len(games), 'errors', errs, round(time.time() - t0), 's', flush=True)
    print('teacher seats', len(games), 'teams', {t: sum(1 for g in games if g['team'] == t) for t in TEACHERS}, flush=True)
    random.shuffle(games)
    nv = max(2, len(games) // 20)
    val, tr = games[:nv], games[nv:]

    def cat_games(gs):
        off = 0; U = {k: [] for k in ('u_step', 'u_x', 'u_y', 'u_k', 'u_inv', 'u_a', 'u_q')}
        S = {k: [] for k in ('cats', 'rcats', 'nums', 'ucnt', 'glob', 'mk')}
        for g in gs:
            for k in S: S[k].append(g[k])
            U['u_step'].append(g['u_step'] + off)
            for k in ('u_x', 'u_y', 'u_k', 'u_inv', 'u_a', 'u_q'): U[k].append(g[k])
            off += len(g['cats'])
        S = {k: np.concatenate(v) for k, v in S.items()}; U = {k: np.concatenate(v) for k, v in U.items()}
        return S, U
    Str, Utr = cat_games(tr); Sva, Uva = cat_games(val)
    print('train steps', len(Str['cats']), 'unit samples', len(Utr['u_a']), 'val steps', len(Sva['cats']), flush=True)
    dev = 'cuda'
    NA, NQ, NG = len(UA), len(QTY), Str['glob'].shape[1]
    H = HIDDEN

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.c0 = nn.Conv2d(C_GRID, H, 3, padding=1); self.c1 = nn.Conv2d(H, H, 3, padding=1)
            self.c2 = nn.Conv2d(H, H, 3, padding=1); self.c3 = nn.Conv2d(H, H, 3, padding=1)
            self.g = nn.Linear(NG, H)
            self.u1 = nn.Linear(5 * H + H + H + N_UNIT, 256); self.ua = nn.Linear(256, NA); self.uq = nn.Linear(256, NQ)
            self.m1 = nn.Linear(2 * H, 256)
            self.mh = nn.ModuleDict({('mh_' + n): nn.Linear(256, s) for n, s in zip(MARKET_HEADS, MARKET_SIZES)})

        def trunk(self, grid, glob):
            h = grid
            for c in (self.c0, self.c1, self.c2, self.c3):
                h = F.relu(c(h))
            return h, F.relu(self.g(glob)), h.mean((2, 3))

    net = Net().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)

    def grids(S, idx):
        cats = torch.as_tensor(S['cats'][idx], device=dev).long(); rc = torch.as_tensor(S['rcats'][idx], device=dev).long()
        nums = torch.as_tensor(S['nums'][idx], device=dev).float() / 50.0
        uc = torch.as_tensor(S['ucnt'][idx], device=dev).float() / 3.0
        B = len(idx)
        g = torch.zeros(B, C_GRID, 100, device=dev)
        g.scatter_(1, cats[:, None, :], 1.0)
        g[:, 13:24] = nums
        g.scatter_(1, (rc + 24)[:, None, :], 1.0)
        g[:, 37] = uc
        return g.view(B, C_GRID, 10, 10), torch.as_tensor(S['glob'][idx].astype(np.float32), device=dev)

    # unit samples grouped by step
    def unit_index(U, nsteps):
        order = np.argsort(U['u_step'], kind='stable')
        starts = np.searchsorted(U['u_step'][order], np.arange(nsteps + 1))
        return order, starts
    otr, sttr = unit_index(Utr, len(Str['cats'])); ova, stva = unit_index(Uva, len(Sva['cats']))
    wa = torch.ones(NA, device=dev)

    def batch_loss(S, U, order, starts, idx, train=True):
        grid, glob = grids(S, idx)
        h, gv, pooled = net.trunk(grid, glob)
        hp = F.pad(h, (1, 1, 1, 1))
        sel = np.concatenate([order[starts[i]:starts[i + 1]] for i in idx]) if len(idx) else np.zeros(0, np.int64)
        local = np.concatenate([np.full(starts[i + 1] - starts[i], j) for j, i in enumerate(idx)]) if len(idx) else np.zeros(0, np.int64)
        if len(sel) == 0:
            return None
        li = torch.as_tensor(local, device=dev).long()
        x = torch.as_tensor(U['u_x'][sel].astype(np.int64), device=dev); y = torch.as_tensor(U['u_y'][sel].astype(np.int64), device=dev)
        feats = [hp[li, :, y + 1, x + 1], hp[li, :, y, x + 1], hp[li, :, y + 2, x + 1], hp[li, :, y + 1, x + 2], hp[li, :, y + 1, x]]
        uv = torch.zeros(len(sel), N_UNIT, device=dev)
        uv[torch.arange(len(sel)), x] = 1.0; uv[torch.arange(len(sel)), 10 + y] = 1.0
        uv[torch.arange(len(sel)), 20 + torch.as_tensor(U['u_k'][sel].astype(np.int64), device=dev)] = 1.0
        uv[:, 36:48] = torch.as_tensor(U['u_inv'][sel].astype(np.float32), device=dev) / 10.0
        z = F.relu(net.u1(torch.cat(feats + [pooled[li], gv[li], uv], 1)))
        ya = torch.as_tensor(U['u_a'][sel].astype(np.int64), device=dev); yq = torch.as_tensor(U['u_q'][sel].astype(np.int64), device=dev)
        la = F.cross_entropy(net.ua(z), ya, weight=wa)
        pick = (ya >= UA.index('PICKUP_WHEAT')) & (ya <= UA.index('PICKUP_SHEEP'))
        lq = F.cross_entropy(net.uq(z)[pick], yq[pick]) if pick.any() else torch.zeros((), device=dev)
        m = F.relu(net.m1(torch.cat([pooled, gv], 1)))
        mk = torch.as_tensor(S['mk'][idx].astype(np.int64), device=dev)
        lm = sum(F.cross_entropy(net.mh['mh_' + n](m), mk[:, j]) for j, n in enumerate(MARKET_HEADS))
        stats = None
        if not train:
            pa = net.ua(z).argmax(1)
            stats = dict(correct=(pa == ya).float().sum().item(), n=len(ya), cls=[(int(a), int(b)) for a, b in zip(ya.tolist(), pa.tolist())],
                         mk_correct=[(net.mh['mh_' + n](m).argmax(1) == mk[:, j]).float().mean().item() for j, n in enumerate(MARKET_HEADS)])
        return la + lq + 0.3 * lm, stats

    nsteps = len(Str['cats']); B = 128
    for ep in range(EPOCHS):
        net.train(); perm = np.random.permutation(nsteps); tl = 0.0; nb = 0
        for i in range(0, nsteps, B):
            out = batch_loss(Str, Utr, otr, sttr, perm[i:i + B])
            if out is None: continue
            loss, _ = out
            opt.zero_grad(); loss.backward(); opt.step(); tl += float(loss); nb += 1
        net.eval(); corr = n = 0; conf = {}; mkc = []
        with torch.no_grad():
            for i in range(0, len(Sva['cats']), 256):
                out = batch_loss(Sva, Uva, ova, stva, np.arange(i, min(i + 256, len(Sva['cats']))), train=False)
                if out is None: continue
                st = out[1]; corr += st['correct']; n += st['n']; mkc.append(st['mk_correct'])
                for a, b in st['cls']:
                    e = conf.setdefault(UA[a], [0, 0]); e[0] += int(a == b); e[1] += 1
        mk_acc = np.mean(np.asarray(mkc), 0) if mkc else []
        print('epoch', ep, 'loss', round(tl / max(1, nb), 4), 'val unit acc', round(corr / max(1, n), 4),
              'per-class', {k: round(v[0] / v[1], 3) for k, v in sorted(conf.items(), key=lambda kv: -kv[1][1])[:14]},
              'market', {nm: round(float(a), 3) for nm, a in zip(MARKET_HEADS, mk_acc)}, round(time.time() - t0), 's', flush=True)
    W = {k: v.detach().cpu().numpy().astype(np.float32) for k, v in net.state_dict().items()}
    W = {k.replace('mh.mh_', 'mh_'): v for k, v in W.items()}
    np.savez_compressed('/kaggle/working/bc_model.npz', **W)
    print('saved', round(time.time() - t0), 's', flush=True)


if __name__ == '__main__':
    main()
