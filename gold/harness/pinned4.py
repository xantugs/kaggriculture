"""Pinned-world counterfactual on recorded ladder games.

Our seat replays its recorded actions for steps < S (the candidate still observes them), then the candidate plays;
the opponent replays its recorded tape. From day S//24 on, the town's shop draws are pinned to the recorded
sequence and the opponent's weeds to its recorded spawns, while our weeds come from a private stream, so every
candidate faces the same town and the same opponent farm whatever it leaves empty.

usage: pinned.py games.json[,more.json] S cand1,cand2 out.jsonl [team=offhand] [maxgames]"""
import sys, os, json, random, time
from concurrent.futures import ProcessPoolExecutor
HERE = '/home/user/kaggriculture/moon'
sys.path.insert(0, os.path.join(HERE, '..', 'arena'))


def _tape(acts, p):
    def f(obs, cfg=None):
        t = obs['step']
        a = acts[t + 1][p] if t + 1 < len(acts) else None
        return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
    return f


def _prefixed(inner, acts, P, S):
    def f(obs, cfg=None):
        a = inner(obs, cfg)
        t = obs['step']
        if t < S:
            r = acts[t + 1][P] if t + 1 < len(acts) else None
            return r if isinstance(r, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        return a
    return f


def reference(d):
    """Replay the recorded game; return per-day spawned weeds for each farm, the shop list, and rewards."""
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    spawns = {}
    orig = K._spawn_weeds
    cur = {'day': 0, 'farm': 0}
    def sw(farm, bs, chance, rng):
        before = {(x, y) for y in range(bs) for x in range(bs) if isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('kind') == 'WEED'}
        orig(farm, bs, chance, rng)
        after = {(x, y) for y in range(bs) for x in range(bs) if isinstance(farm['tiles'][y][x], dict) and farm['tiles'][y][x].get('kind') == 'WEED'}
        spawns[(cur['day'], cur['farm'])] = sorted(after - before)
        cur['farm'] += 1
    oe = K._end_of_day
    def eod(state, env, day):
        cur['day'] = day; cur['farm'] = 0
        return oe(state, env, day)
    K._spawn_weeds = sw; K._end_of_day = eod
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[_tape(d['acts'], 0), _tape(d['acts'], 1)])
    finally:
        K._spawn_weeds = orig; K._end_of_day = oe
    return spawns, list(r['shops']), r['r']


def install_pinned(from_day, opp_seat, spawns, shops):
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    orig_eod = K._end_of_day
    def eod(state, env, day):
        if day < from_day:
            return orig_eod(state, env, day)
        obs0 = state[0].observation
        cfg = env.configuration
        bs = int(K.get(cfg, "boardSize", 10)); tpd = max(1, int(K.get(cfg, "turnsPerDay", 24)))
        chance = float(K.get(cfg, "weedSpawnChance", 0.005)); cap = int(K.get(cfg, "shedCapacity", 100))
        seed = env.info.get("seed", 0)
        for pid, farm in enumerate(obs0.farms):
            private = state[pid].observation.private
            K._daily_refresh_plants(farm, day, tpd)
            K._daily_refresh_animals(farm, day)
            if pid == opp_seat:
                for (x, y) in spawns.get((day, pid), []):
                    if farm['tiles'][y][x] is None:
                        farm['tiles'][y][x] = {"kind": "WEED"}
            else:
                rng = random.Random((seed * 1_000_003) ^ (day * 7919) ^ ((pid + 1) * 104_729))
                K._spawn_weeds(farm, bs, chance, rng)
            K._drop_inventories_to_shed(private, cap)
            farm["farmer"] = list(K._default_spawn(bs)); farm["hands"] = []; farm["hires_today"] = 0
            private["inventories"] = [{}]
        nd = day + 1
        town = obs0.town
        if nd > 0 and nd % 3 == 0 and len(town["unlocked_shops"]) < K.MAX_SHOP_INSTANCES:
            k = len(town["unlocked_shops"])
            town["unlocked_shops"].append(shops[k] if k < len(shops) else "BAKERY")
    K._end_of_day = eod
    return orig_eod


def job(t):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, idx, team, cand, S = t
    d = json.load(open(path, encoding='utf-8'))[idx]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, rref = reference(d)
    rec_ok = [int(x) for x in rref] == [int(x) for x in d['rewards']]
    orig = install_pinned(S // 24, O, spawns, shops)
    import collections
    led = [collections.Counter(), collections.Counter()]
    FARMS = [None, None]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL': led[i][item] += price
            elif op == 'BUY_PRODUCT': led[i][item] -= price
            elif op == 'BUY_SEED': led[i]['seed'] -= price
            elif op == 'BUY_ANIMAL': led[i]['anim'] -= price
        return ok
    opm = K._process_market
    def pm(state, env):
        if state[0].observation.step >= S:
            FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    K._commit_unit = commit; K._process_market = pm
    try:
        A = lean.load(cand)
        ag = [None, None]
        ag[P] = _prefixed(A, d['acts'], P, S)
        ag[O] = _tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm
    tel = getattr(A, 'telemetry', None)
    tel = {k: v for k, v in tel.items() if isinstance(v, (int, float, str))} if isinstance(tel, dict) else None
    return dict(led_us=dict(led[P]), led_them=dict(led[O]), gid=d['id'], opp=names[O], cand=cand, S=S, rec=d['rewards'][P] - d['rewards'][O], rec_ok=rec_ok,
                us=r['r'][P], them=r['r'][O], m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None, err=r['err'], tel=tel)


if __name__ == '__main__':
    files = sys.argv[1].split(','); S = int(sys.argv[2]); cands = sys.argv[3].split(','); out = sys.argv[4]
    team = sys.argv[5] if len(sys.argv) > 5 else 'offhand'
    maxg = int(sys.argv[6]) if len(sys.argv) > 6 else 10 ** 6
    games = []
    for f in files:
        for i, d in enumerate(json.load(open(f, encoding='utf-8'))):
            if team in d['info']['TeamNames']:
                games.append((f, i))
    games = games[:maxg]
    jobs = [(f, i, team, c, S) for f, i in games for c in cands]
    t0 = time.time(); res = []
    with ProcessPoolExecutor(int(os.environ.get("NPROC","4"))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for r in ex.map(job, jobs):
            res.append(r); fh.write(json.dumps(r, ensure_ascii=False) + '\n'); fh.flush()
    for c in cands:
        rs = [r for r in res if r['cand'] == c and r['m'] is not None]
        w = sum(r['m'] > 0 for r in rs); n = max(1, len(rs))
        keys = sorted(set(k for r in rs for k in list(r['led_us']) + list(r['led_them'])))
        print('   us  :', ' '.join(f"{k[:5]} {sum(r['led_us'].get(k,0) for r in rs)/n:.0f}" for k in keys))
        print('   them:', ' '.join(f"{k[:5]} {sum(r['led_them'].get(k,0) for r in rs)/n:.0f}" for k in keys))
        print(f"{c}: {w}-{len(rs)-w} of {len(rs)}  margin {sum(r['m'] for r in rs)/n:+.0f}  us {sum(r['us'] for r in rs)/n:.0f}  them {sum(r['them'] for r in rs)/n:.0f}  rec {sum(r['rec'] for r in rs)/n:+.0f}  recOK {sum(r['rec_ok'] for r in rs)}/{len(rs)}  wall {time.time()-t0:.0f}s")
