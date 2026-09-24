"""Product leak audit from day D0, both seats (decoupled closed loop), mean over seeds.
stock0 + harvested + bought = sold + fed/used + lost_eod + lost_drop + end_shed + end_carried
usage: leak.py A.py B.py seeds [D0]"""
import sys, collections, multiprocessing as mp
sys.path.insert(0, '/home/user/kaggriculture/arena')
PRODS = ['WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'EGG', 'MILK', 'WOOL', 'FERTILIZER']


def run(args):
    A0, B0, seed, D0 = args
    import lean, decouple
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    decouple.install(0)
    A = lean.load(A0); B = lean.load(B0)
    C = [collections.Counter(), collections.Counter()]
    PRIVS = [None, None]; DAY = [0]
    oa, oc, od = K._apply_unit_action, K._commit_unit, K._drop_inventories_to_shed

    def who(p):
        return 0 if p is PRIVS[0] else 1

    def apply(farm, private, idx, action, bs, day, tpd, cap=100):
        DAY[0] = day
        if PRIVS[0] is None or day < D0:
            return oa(farm, private, idx, action, bs, day, tpd, cap)
        i = who(private)
        inv = K._farmer_inventory(private, idx)
        before = dict(inv)
        op = action[0] if isinstance(action, list) and action else None
        s0 = dict(private['shed'])
        oa(farm, private, idx, action, bs, day, tpd, cap)
        if op in ('HARVEST', 'COLLECT_FERTILIZER'):
            for k, n in inv.items():
                d = n - before.get(k, 0)
                if d > 0: C[i]['harv_' + k] += d
        elif op == 'DROP':
            for k, n in before.items():
                got = private['shed'].get(k, 0) - s0.get(k, 0)
                if n - got > 0: C[i]['lostdrop_' + k] += n - got
        elif op in ('FEED', 'FERTILIZE'):
            for k, n in before.items():
                d = n - inv.get(k, 0)
                if d > 0: C[i]['used_' + k] += d

    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and PRIVS[0] is not None and DAY[0] >= D0:
            i = who(private)
            if op == 'SELL':
                C[i]['sold_' + item] += 1
                if price <= 1: C[i]['sold1_' + item] += 1
            elif op == 'BUY_PRODUCT': C[i]['bought_' + item] += 1
        return ok

    def drop(private, capacity):
        if PRIVS[0] is None or DAY[0] < D0:
            return od(private, capacity)
        i = who(private)
        before = collections.Counter()
        for inv in private['inventories']:
            for k, n in inv.items(): before[k] += n
        s0 = dict(private['shed'])
        od(private, capacity)
        for k, n in before.items():
            got = private['shed'].get(k, 0) - s0.get(k, 0)
            if n - got > 0:
                C[i]['losteod_' + k] += n - got
                C[i]['losteod_day%d' % DAY[0]] += n - got
    K._apply_unit_action, K._commit_unit, K._drop_inventories_to_shed = apply, commit, drop
    om = K._process_market

    def pm(state, env):
        PRIVS[0], PRIVS[1] = state[0].observation.private, state[1].observation.private
        return om(state, env)
    K._process_market = pm
    ST = {}

    def wrap(ag, seat):
        def f(obs, cfg=None):
            if obs['step'] == D0 * 24:
                ST[seat] = dict(obs['private']['shed'])
            return ag(obs, cfg)
        return f
    st = [None]
    ointerp = K.interpreter

    def interp(state, env):
        st[0] = state
        return ointerp(state, env)
    K.interpreter = interp
    lean.K.interpreter = interp
    lean.play(None, None, seed, agent_objs=[wrap(A, 0), wrap(B, 1)])
    for i in range(2):
        pv = st[0][i].observation.private
        for k, n in pv['shed'].items(): C[i]['endshed_' + k] += n
        for inv in pv['inventories']:
            for k, n in inv.items(): C[i]['endcarry_' + k] += n
        for k, n in ST.get(i, {}).items(): C[i]['stock0_' + k] += n
    return [dict(C[0]), dict(C[1])]


if __name__ == '__main__':
    A0, B0 = sys.argv[1], sys.argv[2]
    s = sys.argv[3]
    seeds = list(range(int(s.split('-')[0]), int(s.split('-')[1]) + 1)) if '-' in s else [int(x) for x in s.split(',')]
    D0 = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    with mp.Pool(4) as p:
        res = p.map(run, [(A0, B0, sd, D0) for sd in seeds])
    for sd, (a, b) in zip(seeds, res):
        byday = {k[len('losteod_day'):]: v for k, v in a.items() if k.startswith('losteod_day')}
        if byday:
            print('seed %d A eod losses by day %s' % (sd, byday))
    T = [collections.Counter(), collections.Counter()]
    for a, b in res:
        T[0].update(a); T[1].update(b)
    n = len(res)
    cols = ['stock0', 'harv', 'bought', 'sold', 'sold1', 'used', 'losteod', 'lostdrop', 'endshed', 'endcarry']
    print('%-11s' % 'product' + ''.join('%9s' % c for c in cols))
    for p in PRODS:
        for i in range(2):
            print('%-9s %s' % (p[:9], 'AB'[i]) + ''.join('%9.1f' % (T[i]['%s_%s' % (c, p)] / n) for c in cols))
    for i in range(2):
        print('eod loss by day', 'AB'[i], ' '.join('%d:%.1f' % (d, T[i]['losteod_day%d' % d] / n) for d in range(D0, 30) if T[i]['losteod_day%d' % d]))
