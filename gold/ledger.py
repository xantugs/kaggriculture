"""Full money ledger, days >= D0, for both seats of decoupled closed-loop games.
usage: ledger.py A.py B.py seeds [D0]   (A in seat 0).  Prints per-game means: revenue/units per product,
wheat/fertilizer purchases, seeds, animals, wages (hires), land, final money."""
import sys, collections, multiprocessing as mp
sys.path.insert(0, '/home/user/kaggriculture/arena')

def run(args):
    A0, B0, seed, D0 = args
    import lean, decouple
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    decouple.install(0)
    A = lean.load(A0); B = lean.load(B0)
    L = [collections.Counter(), collections.Counter()]
    PR = [None, None]; STEP = [0]
    oc, oh, ol = K._commit_unit, K._do_hire, K._do_buy_land
    def who(private):
        return 0 if private is PR[0] else 1
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and PR[0] is not None and STEP[0] // 24 >= D0:
            l = L[who(private)]
            if op == 'SELL': l['rev_' + item] += price; l['n_' + item] += 1
            elif op == 'BUY_PRODUCT': l['buy_' + item] += price; l['nb_' + item] += 1
            elif op == 'BUY_SEED': l['seed_' + item] += price
            elif op == 'BUY_ANIMAL': l['anim_' + item] += price
        return ok
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']
        oh(farm, private, bs, mult)
        if STEP[0] // 24 >= D0:
            l = L[who(private)]
            if farm['money'] < m0: l['wage'] += m0 - farm['money']; l['hires'] += 1
    def land(farm, bs):
        m0 = farm['money']
        ol(farm, bs)
        if STEP[0] // 24 >= D0 and farm['money'] < m0:
            i = 0 if farm is FARMS[0] else 1
            L[i]['land'] += m0 - farm['money']
    FARMS = [None, None]
    om = K._process_market
    def pm(state, env):
        PR[0], PR[1] = state[0].observation.private, state[1].observation.private
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        STEP[0] = state[0].observation.step
        return om(state, env)
    K._commit_unit, K._do_hire, K._do_buy_land, K._process_market = commit, hire, land, pm
    MON = [0, 0]
    def wrap(ag, seat):
        def f(obs, cfg=None):
            if seat == 0 and obs['step'] == D0 * 24:
                MON[0] = obs['farms'][0]['money']; MON[1] = obs['farms'][1]['money']
            return ag(obs, cfg)
        return f
    r = lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
    K._commit_unit, K._do_hire, K._do_buy_land, K._process_market = oc, oh, ol, om
    for i in range(2):
        L[i]['final'] = r['r'][i]
        L[i]['m_D0'] = MON[i]
    return seed, [dict(L[0]), dict(L[1])]

if __name__ == '__main__':
    A0, B0 = sys.argv[1], sys.argv[2]
    s = sys.argv[3]
    seeds = list(range(int(s.split('-')[0]), int(s.split('-')[1]) + 1)) if '-' in s else [int(x) for x in s.split(',')]
    D0 = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    with mp.Pool(4) as p:
        res = p.map(run, [(A0, B0, sd, D0) for sd in seeds])
    n = len(res)
    T = [collections.Counter(), collections.Counter()]
    for sd, (a, b) in res:
        T[0].update(a); T[1].update(b)
    keys = sorted(set(T[0]) | set(T[1]))
    prods = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']
    print('%-12s %9s %9s %9s' % ('item', 'A', 'B', 'A-B'))
    def row(k, lab=None):
        a, b = T[0][k] / n, T[1][k] / n
        print('%-12s %9.0f %9.0f %9.0f' % (lab or k, a, b, a - b))
    for k in ['final', 'm_D0']: row(k)
    for p in prods:
        row('rev_' + p, 'rev ' + p[:7]); row('n_' + p, '  n ' + p[:7])
    for k in keys:
        if k.startswith(('buy_', 'nb_', 'seed_', 'anim_')): row(k)
    for k in ['wage', 'hires', 'land']: row(k)
    print('per-seed final diff:', ' '.join('%d:%+.0f' % (sd, a['final'] - b['final']) for sd, (a, b) in res))
