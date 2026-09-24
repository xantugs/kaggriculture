"""List both seats' SELL fills for chosen products: step, qty, avg price, and the market inventory before."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
decouple.install(0)
from kaggle_environments.envs.kaggriculture import kaggriculture as K
A = lean.load(sys.argv[1]); B = lean.load(sys.argv[2]); seed = int(sys.argv[3]); prods = sys.argv[4].split(',')
PRIVS = [None, None]; STEP = [0]
fills = collections.defaultdict(lambda: [0, 0])
oc = K._commit_unit
def commit(op, item, price, farm, private, market, cap=100):
    ok = oc(op, item, price, farm, private, market, cap)
    if ok and op == 'SELL' and item in prods:
        i = 0 if private is PRIVS[0] else 1
        f = fills[(STEP[0], i, item)]; f[0] += 1; f[1] += price
    return ok
K._commit_unit = commit
om = K._process_market
def pm(state, env):
    PRIVS[0], PRIVS[1] = state[0].observation.private, state[1].observation.private
    STEP[0] = state[0].observation.step
    return om(state, env)
K._process_market = pm
r = lean.play(None, None, seed, agent_objs=[A, B])
print('result', r['r'])
for p in prods:
    for i in (0, 1):
        ev = sorted((s, f[0], f[1] / f[0]) for (s, ii, pp), f in fills.items() if ii == i and pp == p)
        tot = sum(e[1] for e in ev); rev = sum(e[1] * e[2] for e in ev)
        print('%s seat %d: %d sales, %d units, avg %.1f' % (p, i, len(ev), tot, rev / max(1, tot)))
        print('   ' + ' '.join('d%dh%d:%dx%.0f' % (s // 24, s % 24, q, px) for s, q, px in ev if s >= 288))
