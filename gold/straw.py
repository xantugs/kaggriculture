"""Strawberry audit (decoupled): per seat plants alive by day, deaths, harvested units, fertilized events, sold units/price."""
import sys, collections, json
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
PR = [None, None]
st = [collections.Counter(), collections.Counter()]
oa = K._apply_unit_action
def apply(farm, private, idx, action, bs, day, tpd, cap=100):
    i = 0 if private is PR[0] else 1
    tile = None
    pos = K._farmer_position(farm, idx)
    if pos is not None:
        tile = farm['tiles'][pos[1]][pos[0]]
    crop = tile.get('crop') if isinstance(tile, dict) else None
    inv = K._farmer_inventory(private, idx); s0 = inv.get('STRAWBERRY', 0)
    oa(farm, private, idx, action, bs, day, tpd, cap)
    if crop == 'STRAWBERRY' and isinstance(action, list) and action and day >= 12:
        st[i][action[0]] += 1
        if action[0] == 'HARVEST': st[i]['units'] += inv.get('STRAWBERRY', 0) - s0
K._apply_unit_action = apply
oi = K.interpreter
def interp(state, env):
    if getattr(state[0].observation, 'private', None) is not None:
        PR[0], PR[1] = state[0].observation.private, state[1].observation.private
    return oi(state, env)
K.interpreter = interp; lean.K.interpreter = interp
alive = collections.defaultdict(lambda: [0, 0])
def wrap(ag, seat):
    def f(obs, cfg=None):
        if obs['hour'] == 0 and seat == 0:
            for i in (0, 1):
                alive[obs['day']][i] = sum(1 for row in obs['farms'][i]['tiles'] for t in row if isinstance(t, dict) and t.get('crop') == 'STRAWBERRY')
        return ag(obs, cfg)
    return f
r = lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
print('result', r['r'])
for i in (0, 1):
    print('seat', i, dict(st[i]))
print('alive', [(d, alive[d][0], alive[d][1]) for d in sorted(alive) if d >= 11 and d % 2 == 0])
