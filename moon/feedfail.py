"""Log failed FEED commands of seat 0: step, unit, inventory, shed wheat; plus wheat pickups/buys around them."""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); seed = int(sys.argv[2])
B = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'))
FARM0 = [None]; STEP = [0]; LOG = []; buys = collections.Counter()
oa, opm, oc = K._apply_unit_action, K._process_market, K._commit_unit
def hook(farm, private, actor, command, *a, **k):
    if farm is FARM0[0] and command and command[0] == 'FEED':
        inv = dict(private['inventories'][actor]); x, y = (farm['farmer'] if actor == 0 else farm['hands'][actor - 1]); t = farm['tiles'][y][x]
        ok = isinstance(t, dict) and 'animal' in t and not t.get('fed_today') and inv.get('WHEAT', 0) > 0
        if not ok:
            LOG.append((STEP[0] // 24, STEP[0] % 24, actor, inv.get('WHEAT', 0), private['shed'].get('WHEAT', 0),
                        (t.get('animal'), t.get('fed_today')) if isinstance(t, dict) else t))
    return oa(farm, private, actor, command, *a, **k)
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and farm is FARM0[0] and item == 'WHEAT' and op in ('BUY_PRODUCT', 'SELL'): buys[(STEP[0] // 24, STEP[0] % 24, op)] += 1
    return ok
def pm(state, env):
    FARM0[0] = state[0].observation.farms[0]; STEP[0] = state[0].observation.step
    return opm(state, env)
K._apply_unit_action, K._process_market, K._commit_unit = hook, pm, commit
r = lean.play(None, None, seed, agent_objs=[A, B])
print(r['r'], 'failed feeds', len(LOG))
for e in LOG[:25]: print('  day %d h%d unit %d carried_wheat %d shed_wheat %d tile %s' % e)
days = sorted({e[0] for e in LOG})
for d in days[:4]:
    print('  wheat market day', d, {f"h{h}{op[0]}": n for (dd, h, op), n in sorted(buys.items()) if dd == d})
