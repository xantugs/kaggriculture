import json, sys, collections, lean, ident2, pfx
from kaggle_environments.envs.kaggriculture import kaggriculture as K
f, gi, cand, S = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
d = json.load(open(f))[gi]; n = d['info']['TeamNames']; P = n.index('Khantugs Gantulga')
farms = {}; ev = collections.Counter(); fails = []
oa = K._apply_unit_action
def apply(farm, private, idx, action, board_size, day, tpd, cap=100):
    p = farms.get(id(farm))
    if p is not None and isinstance(action, list) and action and action[0] == 'FERTILIZE':
        pos = farm['farmer'] if idx == 0 else (farm['hands'][idx - 1] if idx - 1 < len(farm['hands']) else None)
        if pos is not None:
            tile = farm['tiles'][pos[1]][pos[0]]
            inv = private['inventories'][idx] if idx < len(private['inventories']) else {}
            if isinstance(tile, dict) and tile.get('kind') == 'PLANT':
                ok = inv.get('FERTILIZER', 0) > 0
                ev[('us' if p == P else 'them', ok, tile['crop'])] += 1
                if not ok and p == P: fails.append((day, tile['crop']))
    return oa(farm, private, idx, action, board_size, day, tpd, cap)
oi = K.interpreter
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms: farms[id(o.farms[0])] = 0; farms[id(o.farms[1])] = 1
    return oi(state, env)
K._apply_unit_action = apply; K.interpreter = interp
A = lean.load(cand)
ag = [ident2._tape(d['acts'], 0), ident2._tape(d['acts'], 1)]; ag[P] = pfx.prefixed(A, d['acts'], P, S)
r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
print(cand, 'margin', r['r'][P] - r['r'][1 - P], dict(ev), 'fails', fails)
