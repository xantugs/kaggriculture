"""Track production (harvest units), overflow discards, sales and end stock per product for both seats."""
import sys, json, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
FARMS = [None, None]; PRIVS = [None, None]
lost = [collections.Counter(), collections.Counter()]
sold = [collections.Counter(), collections.Counter()]
rev = [collections.Counter(), collections.Counter()]
harv = [collections.Counter(), collections.Counter()]
od = K._drop_inventories_to_shed
def drop(private, capacity):
    i = 0 if private is PRIVS[0] else 1
    before = collections.Counter()
    for inv in private['inventories']:
        for k, n in inv.items(): before[k] += n
    s0 = dict(private['shed'])
    od(private, capacity)
    for k, n in before.items():
        got = private['shed'].get(k, 0) - s0.get(k, 0)
        if n - got > 0: lost[i][k] += n - got
K._drop_inventories_to_shed = drop
oa = K._apply_unit_action
def apply(farm, private, idx, action, bs, day, tpd, cap=100):
    i = 0 if private is PRIVS[0] else 1
    inv = K._farmer_inventory(private, idx)
    before = dict(inv)
    if isinstance(action, list) and action and action[0] == 'DROP':
        s0 = sum(private['shed'].values()); carried = sum(inv.values())
        oa(farm, private, idx, action, bs, day, tpd, cap)
        s1 = sum(private['shed'].values())
        if carried - (s1 - s0) > 0: lost[i]['DROP_OVERFLOW'] += carried - (s1 - s0)
        return
    oa(farm, private, idx, action, bs, day, tpd, cap)
    if isinstance(action, list) and action and action[0] == 'HARVEST':
        for k, n in inv.items():
            d = n - before.get(k, 0)
            if d > 0: harv[i][k] += d
K._apply_unit_action = apply
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL':
        i = 0 if private is PRIVS[0] else 1
        sold[i][item] += 1; rev[i][item] += price
    return ok
K._commit_unit = commit
om = K._process_market
def pm(state, env):
    PRIVS[0], PRIVS[1] = state[0].observation.private, state[1].observation.private
    return om(state, env)
K._process_market = pm
oi = K.interpreter
def interp(state, env):
    if len(state) > 1 and getattr(state[0].observation, 'private', None) is not None:
        PRIVS[0], PRIVS[1] = state[0].observation.private, state[1].observation.private
    return oi(state, env)
K.interpreter = interp
lean.K.interpreter = interp
r = lean.play(None, None, seed, agent_objs=[A, B], record=True)
fo = r['final_obs']
print('result', r['r'])
for i in (0, 1):
    print('seat', i)
    for p in ['WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER']:
        print('   %-10s harvested %4d  sold %4d  rev %7d  avgpx %6.1f  lost %3d' % (p, harv[i][p], sold[i][p], rev[i][p], rev[i][p]/max(1,sold[i][p]), lost[i][p]))
    print('   drop overflow', lost[i]['DROP_OVERFLOW'])
