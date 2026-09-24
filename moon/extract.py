"""Imitation data from recorded games: per (game, seat, day) start-of-day features and the jobs that seat's units
actually completed on each tile that day, plus day-level decisions.
usage: extract.py games.jsonl out.jsonl.gz [procs]
Each output line: {g, s, team, opp, w, m, d, c, n, r, G, y, D}
  y : per-tile bitmask over feat.LABELS (successful actions only)
  D : {hires, land, anim{A:n}, sell{P:n}, buyp{P:n}, seed{C:n}}"""
import sys, os, json, gzip, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import feat

TILE_OPS = {'WATER', 'HARVEST', 'FERTILIZE', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'DIG', 'PLANT', 'BUILD_COOP', 'BUILD_PASTURE', 'PLACE'}


def label_of(action):
    op = action[0]
    if op == 'PLANT':
        return 'PLANT_' + str(action[1]) if len(action) > 1 else None
    if op == 'PLACE':
        return ('PLACE_' + str(action[1])) if len(action) > 1 and action[1] in feat.ANIMALS else None
    return op if op in feat.LABEL_I else None


def one(line):
    import lean
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
                y[(s, day, yy * 10 + x)] |= 1 << feat.LABEL_I[lab]
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
                X[(p, t // 24)] = feat.features(obs, p)
            a = acts[t + 1][p] if t + 1 < len(acts) else None
            return a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
        return f

    K._apply_unit_action = apply; K._do_hire = hire; K._do_buy_land = land; K._commit_unit = commit; K.interpreter = interp
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[tape(0), tape(1)])
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


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    procs = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    lines = [l for l in open(src, encoding='utf-8') if l.strip()]
    ok = bad = 0
    with ProcessPoolExecutor(procs) as ex, gzip.open(dst, 'wt', encoding='utf-8') as fh:
        for rows in ex.map(one, lines, chunksize=2):
            if rows:
                ok += 1
                fh.write('\n'.join(rows) + '\n')
            else:
                bad += 1
    print('games ok', ok, 'not reproduced', bad)
