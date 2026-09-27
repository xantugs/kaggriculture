"""Recorded games of one class: successful plantings per day and crop (us / them) and noon market prices of
TOMATO / STRAWBERRY / CARROT per day, plus tomato-shop count. usage: plantprof.py [MIRROR|DIVERGENT]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor
ITEMS = ('TOMATO', 'STRAWBERRY', 'CARROT', 'WHEAT')


def job(fn):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand')
    plants = [collections.Counter(), collections.Counter()]; px = {}; shops = {}
    onp, opm = K._new_plant, K._process_market
    cur = {'farm': None, 'farms': None}
    def np_(crop, day, tpd):
        t = onp(crop, day, tpd)
        who = 0 if cur['farms'] is None else None
        plants_key[0].append((crop, day))
        return t
    plants_key = [[]]
    oua = K._apply_unit_action
    def ua(farm, private, idx, action, bs, day, tpd, cap=100):
        before = isinstance(action, list) and action and action[0] == 'PLANT'
        pre = farm['tiles'][farm['farmer'][1]][farm['farmer'][0]] if idx == 0 else None
        pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
        tile_before = farm['tiles'][pos[1]][pos[0]] if (before and pos) else 'x'
        oua(farm, private, idx, action, bs, day, tpd, cap)
        if before and pos and tile_before is None and isinstance(farm['tiles'][pos[1]][pos[0]], dict):
            plants[0 if farm is cur['farms'][P] else 1][(day, action[1])] += 1
    def pm(state, env):
        o = state[0].observation; cur['farms'] = o.farms
        if o.step % 24 == 12:
            px[o.step // 24] = {it: o.market['prices'][it] for it in ITEMS}
            shops[o.step // 24] = sum(1 for s in o.town['unlocked_shops'] if 'TOMATO' in K.SHOPS[s])
        return opm(state, env)
    # farms reference for unit actions is set in interpreter before market; hook interpreter-level via _process_market of previous step
    K._apply_unit_action, K._process_market = ua, pm
    try:
        # prime cur['farms'] on step 0 via a wrapper around _initialize
        oi = K._initialize
        def ini(state, env):
            r = oi(state, env); cur['farms'] = state[0].observation.farms; return r
        K._initialize = ini
        lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._apply_unit_action, K._process_market, K._initialize = oua, opm, oi
    return d['id'], [dict((f'{k[0]}|{k[1]}', v) for k, v in c.items()) for c in plants], px, shops


if __name__ == '__main__':
    klass = sys.argv[1] if len(sys.argv) > 1 else 'MIRROR'
    cls = json.load(open(os.path.join(HERE, 'gameclass.json')))
    files = [f for f in json.load(open(os.path.join(HERE, 'g2800_list.json')))
             if (cls.get(os.path.basename(f)[:-5], 0) >= 0.8) == (klass == 'MIRROR')]
    P = [collections.Counter(), collections.Counter()]; PX = collections.defaultdict(list); SH = collections.defaultdict(list)
    res = {}
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '14'))) as ex:
        for gid, pl, px, sh in ex.map(job, files):
            res[gid] = dict(pl=pl, px=px, sh=sh)
            for w in (0, 1):
                for k, v in pl[w].items():
                    P[w][k] += v
            for dd, v in px.items():
                PX[dd].append(v)
            for dd, v in sh.items():
                SH[dd].append(v)
    json.dump(res, open(os.path.join(HERE, 'plantprof_%s.json' % klass), 'w'))
    g = len(files)
    print(f'{klass} games {g}: plantings per game (us/them) and median noon prices')
    for day in range(30):
        row = []
        for crop in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON'):
            a, b = P[0].get(f'{day}|{crop}', 0) / g, P[1].get(f'{day}|{crop}', 0) / g
            if a or b:
                row.append(f'{crop[:3]} {a:4.1f}/{b:4.1f}')
        pr = PX.get(day, [])
        med = lambda it: sorted(v[it] for v in pr)[len(pr) // 2] if pr else 0
        ts = sorted(SH.get(day, [0]))
        print(f'd{day:02d} px T {med("TOMATO"):4d} S {med("STRAWBERRY"):4d} C {med("CARROT"):3d} W {med("WHEAT"):3d} tshops {ts[len(ts) // 2]}  ' + '  '.join(row))
