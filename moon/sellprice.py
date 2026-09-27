"""Our sold units and average price per product (and per 5-day window), and hires per day, pinned from S.
usage: sellprice.py cand S [N]"""
import sys, os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))
from concurrent.futures import ProcessPoolExecutor


def job(t):
    fn, cand, S = t
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    P = d['info']['TeamNames'].index('offhand'); O = 1 - P
    spawns, shops, _ = pinned.reference(d)
    orig = pinned.install_pinned(S // 24, O, spawns, shops)
    st = collections.Counter(); FARM = [None, None]; STEP = [0]
    ocu, opm, odh = K._commit_unit, K._process_market, K._do_hire
    def cu(op, item, price, farm, private, market, cap=100):
        ok = ocu(op, item, price, farm, private, market, cap)
        if ok and op in ('SELL', 'BUY_PRODUCT'):
            who = 'us' if farm is FARM[0] else 'them'
            w = STEP[0] // 24 // 5
            st[(who, op, item, 'n')] += 1; st[(who, op, item, '$')] += price
            st[(who, op, item, 'n', w)] += 1; st[(who, op, item, '$', w)] += price
        return ok
    def dh(farm, private, board, mult=1):
        if farm is FARM[0] and STEP[0] >= S:
            st[('us', 'hire', STEP[0] // 24)] += 1
        return odh(farm, private, board, mult)
    def pm(state, env):
        FARM[0] = state[0].observation.farms[P]; STEP[0] = int(state[0].observation.step)
        return opm(state, env)
    K._commit_unit, K._process_market, K._do_hire = cu, pm, dh
    try:
        A = lean.load(cand)
        ag = [None, None]; ag[P] = pinned._prefixed(A, d['acts'], P, S); ag[O] = pinned._tape(d['acts'], O)
        lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit, K._process_market, K._do_hire = ocu, opm, odh
    return {'|'.join(map(str, k)): v for k, v in st.items()}


if __name__ == '__main__':
    cand, S = sys.argv[1], int(sys.argv[2]); N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    files = json.load(open(os.path.join(HERE, os.environ.get('GLIST', 'g2800_list.json'))))[:N]
    path = os.path.join(HERE, '..', 'arena', 'cand', cand + '.py')
    tot = collections.Counter()
    with ProcessPoolExecutor(int(os.environ.get('WORKERS', '15'))) as ex:
        for r in ex.map(job, [(f, path, S) for f in files]):
            tot.update(r)
    g = len(files)
    for who in ('us', 'them'):
        for op in ('SELL', 'BUY_PRODUCT'):
            for item in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON', 'EGG', 'MILK', 'WOOL', 'FERTILIZER'):
                n = tot.get(f'{who}|{op}|{item}|n', 0)
                if not n:
                    continue
                ws = '  '.join(f"d{5*w}-{5*w+4}: {tot.get(f'{who}|{op}|{item}|n|{w}',0)/g:5.1f}@{tot.get(f'{who}|{op}|{item}|$|{w}',0)/max(1,tot.get(f'{who}|{op}|{item}|n|{w}',0)):5.1f}" for w in range(6) if tot.get(f'{who}|{op}|{item}|n|{w}', 0))
                print(f'{who:4s} {op:11s} {item:10s} {n/g:6.1f}/game @ {tot[f"{who}|{op}|{item}|$"]/n:6.1f}   {ws}')
    print('hires/day:', ' '.join(f"{d}:{tot.get(f'us|hire|{d}',0)/g:.1f}" for d in range(S // 24, 30)))
