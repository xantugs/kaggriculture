"""Replay recorded games; per day (at hour 23) record both farms' money, quadrants, animals by kind, plants by crop,
hands, shed goods value; plus cumulative sales/purchases/hire ledgers per day."""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/arena')

def job(t):
    import pinned4 as PN, lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, idx = t
    d = json.load(open(path))[idx]
    names = d['info']['TeamNames']; P = names.index('offhand'); O = 1 - P
    led = [collections.Counter(), collections.Counter()]
    FARMS = [None, None]; STEP = [0]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            d_ = STEP[0] // 24
            if op == 'SELL': led[i][('S', item, d_)] += price
            elif op == 'BUY_PRODUCT': led[i][('B', item, d_)] += price
            elif op == 'BUY_SEED': led[i][('seed', item, d_)] += price
            elif op == 'BUY_ANIMAL': led[i][('anim', item, d_)] += price
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            led[i][('hire', '', STEP[0] // 24)] += m0 - farm['money']
    opm = K._process_market
    SNAP = {}
    def pm(state, env):
        o = state[0].observation
        FARMS[0], FARMS[1] = o.farms[0], o.farms[1]
        STEP[0] = o.step
        if o.step % 24 == 23:
            snap = []
            for i in (P, O):
                f = o.farms[i]
                an = collections.Counter(); pl = collections.Counter()
                for row in f['tiles']:
                    for tl in row:
                        if isinstance(tl, dict):
                            if 'animal' in tl: an[tl['animal']] += 1
                            elif tl.get('kind') == 'PLANT': pl[tl['crop']] += 1
                            elif tl.get('kind') in ('COOP', 'PASTURE'): an['empty_' + tl['kind']] += 1
                shed = dict(state[i].observation.private['shed'])
                snap.append(dict(money=float(f['money']), quads=list(f['unlocked_quadrants']), an=dict(an), pl=dict(pl),
                                 hands=len(f['hands']), shed=shed))
            SNAP[o.step // 24] = snap
        return opm(state, env)
    K._commit_unit = commit; K._do_hire = hire; K._process_market = pm
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[PN._tape(d['acts'], 0), PN._tape(d['acts'], 1)])
    finally:
        K._commit_unit = oc; K._do_hire = oh; K._process_market = opm
    L = []
    for i in (P, O):
        L.append({'%s|%s|%d' % k: v for k, v in led[i].items()})
    return dict(gid=d['id'], opp=names[O], rew=[d['rewards'][P], d['rewards'][O]], snap=SNAP, led=L, shops=list(r['shops']))

if __name__ == '__main__':
    path = sys.argv[1]; out = sys.argv[2]
    games = [(path, i) for i, d in enumerate(json.load(open(path))) if 'offhand' in d['info']['TeamNames']]
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(out, 'w') as fh:
        for r in ex.map(job, games):
            fh.write(json.dumps(r) + '\n'); fh.flush()
    print('done', len(games))
