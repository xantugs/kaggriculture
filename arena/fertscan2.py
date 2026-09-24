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
        if p is not None and isinstance(action, list) and action and action[0] in ('FERTILIZE', 'PICKUP'):
            pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
            if pos is not None:
                tile = farm['tiles'][pos[1]][pos[0]]
                inv = private['inventories'][idx] if idx < len(private['inventories']) else {}
                w = 'us' if p == P else 'them'
                if action[0] == 'FERTILIZE' and isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                    ok = inv.get('FERTILIZER', 0) > 0
                    ev[(w, 'fert_' + ('ok' if ok else 'FAIL'), tile['crop'])] += 1
                elif action[0] == 'PICKUP' and len(action) > 1 and action[1] in ('FERTILIZER', 'WHEAT'):
                    shed = private['shed'].get(action[1], 0); want = int(action[2]) if len(action) > 2 else 1
                    if shed < want: ev[(w, 'short_' + action[1])] += want - shed
        return oa(farm, private, idx, action, board_size, day, tpd, cap)
    oi = K.interpreter
    def interp(state, env):
        o = state[0].observation
        if hasattr(o, 'farms') and o.farms: farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1
        return oi(state, env)
    K._apply_unit_action = apply; K.interpreter = interp
    try:
        lean.play(None, None, d['info']['seed'], agent_objs=[ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)])
    finally:
        K._apply_unit_action = oa; K.interpreter = oi
    return d['id'], n[1 - P][:14], d['rewards'][P] - d['rewards'][1 - P], f, {'|'.join(k): v for k, v in ev.items()}
if __name__ == '__main__':
    ds = json.load(open(sys.argv[1]))
    out = open(sys.argv[2], 'w')
    with ProcessPoolExecutor(1) as ex:
        for r in ex.map(job, [(f, i) for f, i, _ in ds]):
            out.write(json.dumps(r, ensure_ascii=False) + '\n'); out.flush()
