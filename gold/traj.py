"""Average daily (us - them) money and per-product sales-revenue difference by day over several decoupled seeds."""
import sys, collections
sys.path.insert(0, '/home/user/kaggriculture/arena')
import lean, decouple
from kaggle_environments.envs.kaggriculture import kaggriculture as K
decouple.install(0)
A0 = sys.argv[1]; B0 = sys.argv[2]; seeds = [int(x) for x in sys.argv[3].split(',')]
tot = collections.defaultdict(collections.Counter)
money = collections.defaultdict(float)
for seed in seeds:
    A = lean.load(A0); B = lean.load(B0)
    PR = [None, None]; STEP = [0]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100, oc=oc, PR=PR, STEP=STEP):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and PR[0] is not None:
            i = 0 if private is PR[0] else 1
            sgn = 1 if i == 0 else -1
            d = STEP[0] // 24
            if op == 'SELL': tot[d][item] += sgn * price
            elif op in ('BUY_PRODUCT',): tot[d][item] -= sgn * price
            elif op == 'BUY_SEED': tot[d]['seed'] -= sgn * price
            elif op == 'BUY_ANIMAL': tot[d]['anim'] -= sgn * price
        return ok
    K._commit_unit = commit
    om = K._process_market
    def pm(state, env, om=om, PR=PR, STEP=STEP):
        PR[0], PR[1] = state[0].observation.private, state[1].observation.private
        STEP[0] = state[0].observation.step
        return om(state, env)
    K._process_market = pm
    def wrap(ag, seat):
        def f(obs, cfg=None):
            if seat == 0 and obs['hour'] == 0:
                money[obs['day']] += obs['farms'][0]['money'] - obs['farms'][1]['money']
            return ag(obs, cfg)
        return f
    lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
    K._commit_unit = oc; K._process_market = om
n = len(seeds)
prods = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER', 'seed', 'anim']
print('day  money_diff ' + ' '.join('%7s' % p[:6] for p in prods))
for d in range(10, 30):
    print('%3d %10.0f ' % (d, money[d] / n) + ' '.join('%7.0f' % (tot[d][p] / n) for p in prods))
