"""Log failed PICKUP / FERTILIZE commands of seat 0 with shed stock at that moment."""
import sys, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); seed = int(sys.argv[2])
B = lean.load(os.path.join(HERE, '..', 'arena', 'cand', 'omw_v15b.py'))
F = [None]; S = [0]; LOG = []; kinds = collections.Counter()
oa, opm = K._apply_unit_action, K._process_market
def hook(farm, private, actor, command, *a, **k):
    if farm is F[0] and command and command[0] in ('PICKUP', 'FERTILIZE') and S[0] >= int(os.environ.get('PF_FROM', '360')):
        inv = dict(private['inventories'][actor]); shed = dict(private['shed'])
        r = oa(farm, private, actor, command, *a, **k)
        if dict(private['inventories'][actor]) == inv:
            kinds[(command[0], command[1] if len(command) > 1 else '')] += 1
            LOG.append((S[0] // 24, S[0] % 24, actor, command, shed.get(command[1], 0) if command[0] == 'PICKUP' else inv.get('FERTILIZER', 0)))
        return r
    return oa(farm, private, actor, command, *a, **k)
def pm(state, env):
    F[0] = state[0].observation.farms[0]; S[0] = state[0].observation.step
    return opm(state, env)
K._apply_unit_action, K._process_market = hook, pm
lean.play(None, None, seed, agent_objs=[A, B])
print('failures by kind', dict(kinds))
for e in LOG[:20]: print('  day %d h%d unit %d %s stock/inv %s' % e)
