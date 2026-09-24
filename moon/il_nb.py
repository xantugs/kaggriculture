# Kaggriculture imitation planner: extract tile-job labels from top-tier episodes, train a per-tile network.
import subprocess, sys, os, json
import importlib.metadata as _md
try:
    _v = _md.version('kaggle-environments')
except Exception:
    _v = None
print('preinstalled kaggle-environments', _v, flush=True)
if _v != '1.32.7':
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '--force-reinstall', '--no-deps', 'kaggle-environments==1.32.7'], check=False)
print('now', _md.version('kaggle-environments'), flush=True)
MAX_GAMES = 2000
EPOCHS = 30
HIDDEN = 64
MIN_DAY = 6

# ---- feat.py ----


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


# ---- extraction ----

import sys, os, json, gzip, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))

TILE_OPS = {'WATER', 'HARVEST', 'FERTILIZE', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'DIG', 'PLANT', 'BUILD_COOP', 'BUILD_PASTURE', 'PLACE'}


def label_of(action):
    op = action[0]
    if op == 'PLANT':
        return 'PLANT_' + str(action[1]) if len(action) > 1 else None
    if op == 'PLACE':
        return ('PLACE_' + str(action[1])) if len(action) > 1 and action[1] in ANIMALS else None
    return op if op in LABEL_I else None


def one(line):
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.loads(line)
    names = d['info'].get('TeamNames') or ['?', '?']
    acts = d['acts']
    FARMS = [None, None]; STEP = [0]
    y = collections.defaultdict(int)            # (seat, day, tile) -> bitmask
    D = collections.defaultdict(lambda: dict(hires=0, land=0, anim=collections.Counter(), sell=collections.Counter(),
                                             buyp=collections.Counter(), seed=collections.Counter()))
    X = {}

    def seat_of(farm):
        return 0 if farm is FARMS[0] else (1 if farm is FARMS[1] else -1)

    oa = K._apply_unit_action
    def apply(farm, private, idx, action, bs, day, tpd, cap=100):
        lab = label_of(action) if isinstance(action, list) and action and action[0] in TILE_OPS else None
        if lab is None:
            return oa(farm, private, idx, action, bs, day, tpd, cap)
        pos = K._farmer_position(farm, idx)
        if pos is None:
            return oa(farm, private, idx, action, bs, day, tpd, cap)
        x, yy = pos[0], pos[1]
        before = json.dumps(farm['tiles'][yy][x], sort_keys=True)
        inv_before = json.dumps(K._farmer_inventory(private, idx), sort_keys=True)
        oa(farm, private, idx, action, bs, day, tpd, cap)
        changed = json.dumps(farm['tiles'][yy][x], sort_keys=True) != before or (
            action[0] in ('HARVEST', 'COLLECT_FERTILIZER') and json.dumps(K._farmer_inventory(private, idx), sort_keys=True) != inv_before)
        if changed:
            s = seat_of(farm)
            if s >= 0:
                y[(s, day, yy * 10 + x)] |= 1 << LABEL_I[lab]
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        n0 = farm['hires_today']; oh(farm, private, bs, mult)
        if farm['hires_today'] > n0:
            s = seat_of(farm)
            if s >= 0: D[(s, STEP[0] // 24)]['hires'] += 1
    ol = K._do_buy_land
    def land(farm, bs):
        q0 = len(farm['unlocked_quadrants']); ol(farm, bs)
        if len(farm['unlocked_quadrants']) > q0:
            s = seat_of(farm)
            if s >= 0: D[(s, STEP[0] // 24)]['land'] += 1
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok:
            s = seat_of(farm)
            if s >= 0:
                e = D[(s, STEP[0] // 24)]
                key = {'SELL': 'sell', 'BUY_PRODUCT': 'buyp', 'BUY_SEED': 'seed', 'BUY_ANIMAL': 'anim'}.get(op)
                if key: e[key][item] += 1
        return ok
    oi = K.interpreter
    def interp(state, env):
        o = state[0].observation
        if hasattr(o, 'farms') and o.farms:
            FARMS[0], FARMS[1] = o.farms[0], o.farms[1]; STEP[0] = o.get('step', 0)
        return oi(state, env)

    def tape(p):
        def f(obs, cfg=None):
            t = obs['step']
            if t % 24 == 0:
                X[(p, t // 24)] = features(obs, p)
            a = acts[t + 1][p] if t + 1 < len(acts) else None
            return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        return f

    K._apply_unit_action = apply; K._do_hire = hire; K._do_buy_land = land; K._commit_unit = commit; K.interpreter = interp
    try:
        r = play(None, None, d['info']['seed'], agent_objs=[tape(0), tape(1)])
    finally:
        K._apply_unit_action = oa; K._do_hire = oh; K._do_buy_land = ol; K._commit_unit = oc; K.interpreter = oi
    rew = d.get('rewards') or [None, None]
    if [int(v) if v is not None else None for v in r['r']] != [int(v) if v is not None else None for v in rew]:
        return []
    out = []
    for (p, day), (cats, nums, rcats, g) in X.items():
        if day > 28:
            continue
        yy = [y.get((p, day, i), 0) for i in range(100)]
        e = D[(p, day)]
        out.append(json.dumps(dict(g=d['id'], s=p, team=names[p], opp=names[1 - p], w=int(rew[p] > rew[1 - p]),
                                   m=int(rew[p] - rew[1 - p]), d=day, c=cats,
                                   n=[[round(v, 3) for v in row] for row in nums], r=rcats, G=[round(v, 4) for v in g], y=yy,
                                   D=dict(hires=e['hires'], land=e['land'], anim=dict(e['anim']), sell=dict(e['sell']),
                                          buyp=dict(e['buyp']), seed=dict(e['seed']))), ensure_ascii=False))
    return out




# ===================================== notebook driver =====================================
import glob, time, math, random, pickle


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


def load_replay(path):
    rep = json.load(open(path, encoding='utf-8'))
    acts = [[(x.get('action') if isinstance(x, dict) and isinstance(x.get('action'), dict) else None) for x in s]
            for s in rep.get('steps') or []]
    info = rep.get('info') or {}
    eid = int(os.path.basename(path)[:-5]) if os.path.basename(path)[:-5].isdigit() else rep.get('id')
    return json.dumps(dict(id=eid, info=dict(TeamNames=info.get('TeamNames'), seed=info.get('seed')),
                           rewards=rep.get('rewards'), statuses=rep.get('statuses'), acts=acts))


def extract_file(path):
    try:
        rows = one(load_replay(path))
        return rows if rows else ['ERR not reproduced ' + os.path.basename(path)]
    except Exception as e:
        import traceback
        return ['ERR ' + os.path.basename(path) + ' ' + traceback.format_exc()[-600:]]


def main():
    import numpy as np
    import torch
    import torch.nn as nn
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    files = sorted(glob.glob('/kaggle/input/**/*.json', recursive=True))
    files = [f for f in files if os.path.basename(f)[:-5].isdigit()]
    random.seed(0); random.shuffle(files)
    files = files[:MAX_GAMES]
    print('replay files', len(files), flush=True)
    rows = []; ok = 0
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        errs = 0
        for k, rs in enumerate(ex.map(extract_file, files, chunksize=4)):
            if rs and not rs[0].startswith('ERR'):
                ok += 1; rows.extend(rs)
            else:
                errs += 1
                if errs <= 5:
                    print(rs[0] if rs else 'ERR empty', flush=True)
            if k % 100 == 0:
                print('extracted', k, 'games ok', ok, 'rows', len(rows), round(time.time() - t0), 's', flush=True)
    import gzip
    with gzip.open('/kaggle/working/il_rows.jsonl.gz', 'wt', encoding='utf-8') as fh:
        fh.write('\n'.join(rows))
    print('extraction done', ok, 'games', len(rows), 'rows', round(time.time() - t0), 's', flush=True)

    recs = [json.loads(x) for x in rows]
    recs = [x for x in recs if x['w'] == 1 and MIN_DAY <= x['d'] <= 28]
    gids = sorted(set(x['g'] for x in recs)); random.shuffle(gids)
    val_g = set(gids[:max(1, len(gids) // 10)])
    NL = len(LABELS)

    def tensors(rs):
        X = np.zeros((len(rs) * 100, len(tile_inputs([0] * 100, [[0.0] * N_NUM] * 100, [0] * 100, [])[0])), np.float32)
        Gm = np.zeros((len(rs) * 100, len(GLOBAL_NAMES)), np.float32)
        Y = np.zeros((len(rs) * 100, NL), np.float32)
        for j, x in enumerate(rs):
            X[j * 100:(j + 1) * 100] = np.asarray(tile_inputs(x['c'], x['n'], x['r'], x['G']), np.float32)
            Gm[j * 100:(j + 1) * 100] = np.asarray(x['G'], np.float32)[None, :]
            yb = np.asarray(x['y'], np.int64)
            for l in range(NL):
                Y[j * 100:(j + 1) * 100, l] = (yb >> l) & 1
        return X, Gm, Y

    tr = [x for x in recs if x['g'] not in val_g]; va = [x for x in recs if x['g'] in val_g]
    Xtr, Gtr, Ytr = tensors(tr); Xva, Gva, Yva = tensors(va)
    # skip locked tiles (never acted on)
    keep_tr = Xtr[:, CAT_I['LOCKED']] < 0.5; keep_va = Xva[:, CAT_I['LOCKED']] < 0.5
    Xtr, Gtr, Ytr = Xtr[keep_tr], Gtr[keep_tr], Ytr[keep_tr]
    Xva, Gva, Yva = Xva[keep_va], Gva[keep_va], Yva[keep_va]
    gmu, gsd = Gtr.mean(0), Gtr.std(0) + 1e-3
    xmu, xsd = Xtr.mean(0), Xtr.std(0) + 1e-3
    print('train tiles', len(Xtr), 'val tiles', len(Xva), 'label rates', dict(zip(LABELS, np.round(Ytr.mean(0), 4).tolist())), flush=True)

    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    DX, DG, H = Xtr.shape[1], Gtr.shape[1], HIDDEN

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.wx = nn.Linear(DX, H); self.wg = nn.Linear(DG, H, bias=False)
            self.l2 = nn.Linear(H, H); self.out = nn.Linear(H, NL)

        def forward(self, x, g):
            h = torch.relu(self.wx(x) + self.wg(g))
            h = torch.relu(self.l2(h))
            return self.out(h)

    net = Net().to(dev)
    opt = torch.optim.Adam(net.parameters(), lr=2e-3)
    pos = torch.tensor(np.clip((1 - Ytr.mean(0)) / np.maximum(Ytr.mean(0), 1e-4), 1, 30) ** 0.5, device=dev)
    lossf = nn.BCEWithLogitsLoss(pos_weight=pos)
    T = lambda a: torch.tensor(a, device=dev)
    Xt, Gt, Yt = T((Xtr - xmu) / xsd), T((Gtr - gmu) / gsd), T(Ytr)
    Xv, Gv, Yv = T((Xva - xmu) / xsd), T((Gva - gmu) / gsd), T(Yva)
    n = len(Xt); bs = 8192
    for ep in range(EPOCHS):
        net.train(); perm = torch.randperm(n, device=dev); tl = 0.0
        for i in range(0, n, bs):
            b = perm[i:i + bs]
            loss = lossf(net(Xt[b], Gt[b]), Yt[b])
            opt.zero_grad(); loss.backward(); opt.step(); tl += float(loss) * len(b)
        if ep % 5 == 4 or ep == EPOCHS - 1:
            net.eval()
            with torch.no_grad():
                pv = torch.sigmoid(net(Xv, Gv)).cpu().numpy()
            yv = Yva
            f1s = []
            for l in range(NL):
                best = (0, 0.5)
                for th in np.linspace(0.05, 0.95, 19):
                    pr = pv[:, l] > th; tp = (pr & (yv[:, l] > 0.5)).sum(); fp = (pr & (yv[:, l] < 0.5)).sum(); fn = ((~pr) & (yv[:, l] > 0.5)).sum()
                    f1 = 2 * tp / max(1, 2 * tp + fp + fn)
                    if f1 > best[0]: best = (f1, th)
                f1s.append(best)
            print('epoch', ep, 'train loss', round(tl / n, 4), 'val F1', {LABELS[l]: round(f1s[l][0], 3) for l in range(NL)}, flush=True)
    W = {k: v.detach().cpu().numpy().tolist() for k, v in net.state_dict().items()}
    model = dict(labels=LABELS, cats=CATS, global_names=GLOBAL_NAMES, hidden=H, weights=W,
                 xmu=xmu.tolist(), xsd=xsd.tolist(), gmu=gmu.tolist(), gsd=gsd.tolist(),
                 thresholds=[f1s[l][1] for l in range(NL)], val_f1=[f1s[l][0] for l in range(NL)],
                 games=len(gids), min_day=MIN_DAY)
    json.dump(model, open('/kaggle/working/il_model.json', 'w'))
    print('saved model; total', round(time.time() - t0), 's', flush=True)


if __name__ == '__main__':
    main()
