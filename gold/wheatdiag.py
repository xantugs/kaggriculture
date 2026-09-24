"""Wheat flows per seat: harvested, sold (units, rev), bought (units, cost), fed, lost."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean
from kaggle_environments.envs.kaggriculture import kaggriculture as K
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
PRIVS = [None, None]; STEP = [0]
st = [collections.Counter(), collections.Counter()]
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and item == 'WHEAT' and PRIVS[0] is not None:
        i = 0 if private is PRIVS[0] else 1
        if op == 'SELL': st[i]['sold'] += 1; st[i]['rev'] += price
        elif op == 'BUY_PRODUCT': st[i]['bought'] += 1; st[i]['cost'] += price
        elif op == 'BUY_SEED': st[i]['seeds'] += 1
    return ok
K._commit_unit = commit
oa = K._apply_unit_action
def apply(farm, private, idx, action, bs, day, tpd, cap=100):
    i = 0 if private is PRIVS[0] else 1
    inv = K._farmer_inventory(private, idx); w0 = inv.get('WHEAT', 0)
    oa(farm, private, idx, action, bs, day, tpd, cap)
    if isinstance(action, list) and action:
        if action[0] == 'HARVEST' and inv.get('WHEAT', 0) > w0: st[i]['harv'] += inv.get('WHEAT', 0) - w0
        if action[0] == 'FEED' and inv.get('WHEAT', 0) < w0: st[i]['fed'] += 1
K._apply_unit_action = apply
om = K._process_market
def pm(state, env):
    PRIVS[0], PRIVS[1] = state[0].observation.private, state[1].observation.private
    return om(state, env)
K._process_market = pm
oi = K.interpreter
def interp(state, env):
    if getattr(state[0].observation, 'private', None) is not None:
        PRIVS[0], PRIVS[1] = state[0].observation.private, state[1].observation.private
    return oi(state, env)
K.interpreter = interp; lean.K.interpreter = interp
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'])
for i in (0, 1):
    s = st[i]
    print('seat %d harvested %d fed %d sold %d ($%d, avg %.1f) bought %d ($%d, avg %.1f) net $%d seeds %d' % (i, s['harv'], s['fed'], s['sold'], s['rev'], s['rev']/max(1,s['sold']), s['bought'], s['cost'], s['cost']/max(1,s['bought']), s['rev']-s['cost'], s['seeds']))
