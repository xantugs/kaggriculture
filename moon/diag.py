"""Diagnose seat 0: per action type successes/no-ops, and a daily farm summary. usage: diag.py A B seed"""
import sys, os, json, copy, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'arena'))
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3])
SEAT = int(sys.argv[4]) if len(sys.argv) > 4 else 0
ok = collections.Counter(); bad = collections.Counter(); bad_ex = collections.defaultdict(list)
orig = K._apply_unit_action
STEP = [0]
def apply(farm, private, idx, action, bs, day, tpd, cap=100):
    if farm is not FARMS[SEAT] or not isinstance(action, list) or not action:
        return orig(farm, private, idx, action, bs, day, tpd, cap)
    before = json.dumps([farm['tiles'], farm['farmer'], farm['hands'], private['shed'], private['inventories']], sort_keys=True)
    orig(farm, private, idx, action, bs, day, tpd, cap)
    after = json.dumps([farm['tiles'], farm['farmer'], farm['hands'], private['shed'], private['inventories']], sort_keys=True)
    op = action[0]
    if op == 'PASS': return
    if before == after:
        bad[op] += 1
        if len(bad_ex[op]) < 6: bad_ex[op].append((STEP[0], idx, action))
    else: ok[op] += 1
K._apply_unit_action = apply
FARMS = [None, None]
orig_i = K.interpreter
daily = []
def interp(state, env):
    o = state[0].observation
    if hasattr(o, 'farms') and o.farms:
        FARMS[0], FARMS[1] = o.farms[0], o.farms[1]
        STEP[0] = o.get('step', 0)
        if STEP[0] % 24 == 23:
            f = o.farms[SEAT]; c = collections.Counter()
            for row in f['tiles']:
                for t in row:
                    if isinstance(t, dict): c[t.get('crop') or t.get('animal') or t['kind']] += 1
            daily.append((STEP[0] // 24, int(f['money']), len(f['hands']), dict(c), dict((k, v) for k, v in state[SEAT].observation.private['shed'].items() if v)))
    return orig_i(state, env)
K.interpreter = interp
r = lean.play(None, None, seed, agent_objs=[A, B] if SEAT == 0 else [B, A])
print('result', r['r'], r['err'])
print('ok ', dict(ok)); print('bad', dict(bad))
for k, v in bad_ex.items(): print('  ', k, v)
for d in daily: print(d)
