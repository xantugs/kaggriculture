"""Recorded-replay scan: when each farm buys land, its hands, cash, and crop/animal counts per day.
usage: landscan.py [GLIST] -> landscan.json (per game: both seats' day of each land buy, locked/hands/money per day)"""
import sys, os, json, collections
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', 'arena'))


def job(fn):
    import lean, pinned
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d = json.load(open(fn, encoding='utf-8'))[0]
    names = d['info']['TeamNames']; P = names.index('offhand')
    F = [None, None]; STEP = [0]
    land_days = [[], []]; days = [[], []]; seeds = [collections.Counter(), collections.Counter()]
    anim = [collections.Counter(), collections.Counter()]
    oe, opm, oland, ocu = K._end_of_day, K._process_market, K._do_buy_land, K._commit_unit
    cur = [0]

    def seat(farm):
        return 0 if farm is F[P] else 1

    def eod(state, env, day):
        cur[0] = day + 1
        for s, p in ((0, P), (1, 1 - P)):
            f = state[0].observation.farms[p]; c = collections.Counter()
            for row in f['tiles']:
                for t in row:
                    if t == 'LOCKED': c['#'] += 1
                    elif isinstance(t, dict): c[t.get('crop') or t.get('animal') or t.get('kind')] += 1
            days[s].append(dict(m=f['money'], h=len(f['hands']), locked=c['#'], stra=c['STRAWBERRY'], cow=c['COW'],
                                toma=c['TOMATO'], whea=c['WHEAT'], carr=c['CARROT'], melo=c['MELON']))
        return oe(state, env, day)

    def pm(state, env):
        F[0], F[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)

    def land(farm, bs):
        m0 = farm['money']; r = oland(farm, bs)
        if farm['money'] != m0: land_days[seat(farm)].append((cur[0], m0 - farm['money']))
        return r

    def cu(op, it, price, farm, private, market, cap=100):
        ok = ocu(op, it, price, farm, private, market, cap)
        if ok and op == 'BUY_SEED': seeds[seat(farm)][f'{cur[0]}:{it}'] += 1
        if ok and op == 'BUY_ANIMAL': anim[seat(farm)][f'{cur[0]}:{it}'] += 1
        return ok
    K._end_of_day, K._process_market, K._do_buy_land, K._commit_unit = eod, pm, land, cu
    try:
        r = lean.play(None, None, d['info']['seed'], agent_objs=[pinned._tape(d['acts'], 0), pinned._tape(d['acts'], 1)])
    finally:
        K._end_of_day, K._process_market, K._do_buy_land, K._commit_unit = oe, opm, oland, ocu
    return dict(gid=str(d['id']), opp=names[1 - P], rew=[d['rewards'][P], d['rewards'][1 - P]], land=land_days, days=days,
                seeds=[dict(x) for x in seeds], anim=[dict(x) for x in anim])


if __name__ == '__main__':
    files = json.load(open(os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else 'g2800_list.json')))
    with ProcessPoolExecutor(16) as ex:
        rs = list(ex.map(job, files))
    out = sys.argv[2] if len(sys.argv) > 2 else 'landscan.json'
    json.dump(rs, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
    print('games', len(rs), '->', out)
