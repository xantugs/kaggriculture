import json, sys, glob, collections, lean, ident2
from concurrent.futures import ProcessPoolExecutor
from kaggle_environments.envs.kaggriculture import kaggriculture as K
def job(t):
    f, gi = t
    d = json.load(open(f))[gi]; n = d['info']['TeamNames']; P = n.index('Khantugs Gantulga')
    farms = {}; ev = collections.Counter()
    oa = K._apply_unit_action
    def apply(farm, private, idx, action, board_size, day, tpd, cap=100):
        p = farms.get(id(farm))
        if p is not None and isinstance(action, list) and action:
            pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
            if pos is not None:
                tile = farm['tiles'][pos[1]][pos[0]]
                inv = private['inventories'][idx] if idx < len(private['inventories']) else {}
                w = 'us' if p == P else 'them'; op = action[0]
                an = isinstance(tile, dict) and 'animal' in tile
                if op == 'FEED' and an and not tile['fed_today'] and inv.get('WHEAT', 0) <= 0: ev[(w, 'feed_nowheat_d%d' % day)] += 1
                if op == 'PLACE' and len(action) > 1 and action[1] in ('COW', 'SHEEP', 'GOOSE') and inv.get(action[1], 0) <= 0: ev[(w, 'place_noanimal')] += 1
        return oa(farm, private, idx, action, board_size, day, tpd, cap)
    oe = K._daily_refresh_animals
    def dra(farm, day):
        p = farms.get(id(farm))
        if p is not None:
            for row in farm['tiles']:
                for tl in row:
                    if isinstance(tl, dict) and 'animal' in tl and not tl['fed_today'] and tl['consecutive_unfed'] >= 1:
                        ev[('us' if p == P else 'them', 'escape_%s_d%d' % (tl['animal'], day))] += 1
        return oe(farm, day)
    oi = K.interpreter
    def interp(state, env):
        o = state[0].observation
        if hasattr(o, 'farms') and o.farms: farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1
        return oi(state, env)
    K._apply_unit_action = apply; K.interpreter = interp; K._daily_refresh_animals = dra
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)])
    finally:
        K._apply_unit_action = oa; K.interpreter = oi; K._daily_refresh_animals = oe
    return d['id'], n[1 - P][:14], d['rewards'][P] - d['rewards'][1 - P], {'|'.join(k): v for k, v in ev.items()}
if __name__ == '__main__':
    ds = json.load(open(sys.argv[1]))
    tot = collections.Counter(); c = 0
    with ProcessPoolExecutor(1) as ex:
        for gid, opp, m, e in ex.map(job, [(f, i) for f, i, _ in ds]):
            tot.update(e); c += 1
            if any(k.startswith('us') for k in e): print(gid, opp, m, e)
    print(c, dict(tot))
