"""One-time crop audit per seat from day 12: plantings, harvests, units per harvest, and tile-days occupied."""
import sys, collections
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
    pos = K._farmer_position(farm, idx)
    tile = farm['tiles'][pos[1]][pos[0]] if pos is not None else None
    before = dict(tile) if isinstance(tile, dict) else tile
    inv = K._farmer_inventory(private, idx); inv0 = dict(inv)
    oa(farm, private, idx, action, bs, day, tpd, cap)
    if day >= 12 and isinstance(action, list) and action:
        op = action[0]
        if op == 'PLANT' and before is None and isinstance(farm['tiles'][pos[1]][pos[0]], dict):
            st[i]['plant_' + action[1][:5]] += 1
        if op == 'HARVEST' and isinstance(before, dict) and before.get('kind') == 'PLANT' and before['crop'] in ('WHEAT', 'CARROT'):
            got = inv.get(before['crop'], 0) - inv0.get(before['crop'], 0)
            st[i]['harv_' + before['crop'][:5]] += 1; st[i]['units_' + before['crop'][:5]] += got
            st[i]['age_' + before['crop'][:5]] += day - before['planted_day']
            st[i]['fert_' + before['crop'][:5]] += 1 if before.get('fertilized_until_day', -1) >= 0 else 0
K._apply_unit_action = apply
oi = K.interpreter
def interp(state, env):
    if getattr(state[0].observation, 'private', None) is not None:
        PR[0], PR[1] = state[0].observation.private, state[1].observation.private
    return oi(state, env)
K.interpreter = interp; lean.K.interpreter = interp
tile_days = [collections.Counter(), collections.Counter()]
def wrap(ag, seat):
    def f(obs, cfg=None):
        if seat == 0 and obs['hour'] == 12 and obs['day'] >= 12:
            for i in (0, 1):
                for row in obs['farms'][i]['tiles']:
                    for t in row:
                        if isinstance(t, dict) and t.get('kind') == 'PLANT': tile_days[i][t['crop'][:5]] += 1
                        elif t is None: tile_days[i]['empty'] += 1
                        elif isinstance(t, dict) and t.get('kind') == 'WEED': tile_days[i]['weed'] += 1
        return ag(obs, cfg)
    return f
r = lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
print('result', r['r'])
for i in (0, 1):
    s = st[i]
    out = {}
    for c in ('WHEAT', 'CARRO'):
        h = s['harv_' + c]
        out[c] = 'plant %d harv %d units %d (%.2f/harv) age %.1f fertilized %d' % (s['plant_' + c], h, s['units_' + c], s['units_' + c] / max(1, h), s['age_' + c] / max(1, h), s['fert_' + c])
    print('seat', i, out, 'tile-days', dict(tile_days[i]))
