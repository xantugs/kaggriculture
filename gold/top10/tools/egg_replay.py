"""Replay recorded games (both sides recorded) and measure geese / eggs per player per day.
usage: egg_replay.py games.jsonl.gz refs.jsonl out.jsonl
"""
import sys, os, json, gzip, collections, time
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena')

EGG_SHOPS = ('BAKERY', 'BRUNCH_SPOT')


def _play(g):
    import lean
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    acts = g['acts']
    seed = g['info']['seed']
    days = [[], []]
    mk = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    FARMS = [None, None]; DAY = [0]
    oc, opm, oeod = K._commit_unit, K._process_market, K._end_of_day

    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            d = mk[i][DAY[0]]
            if op == 'SELL':
                d['u_' + item] += 1; d['$_' + item] += price
            elif op == 'BUY_ANIMAL':
                d['anim_' + item] += 1
            elif op == 'BUY_PRODUCT':
                d['buy_' + item] += 1; d['$buy_' + item] += price
        return ok

    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        DAY[0] = int(K.get(state[0].observation, 'step', 0)) // 24
        return opm(state, env)

    def eod(state, env, day):
        obs0 = state[0].observation
        shops = list(obs0.town.get('unlocked_shops', []))
        for pid, farm in enumerate(obs0.farms):
            priv = state[pid].observation.private
            c = collections.Counter()
            geese_pos = []
            for y, row in enumerate(farm['tiles']):
                for x, t in enumerate(row):
                    if isinstance(t, dict):
                        if t.get('animal'):
                            a = t['animal']
                            c[a] += 1
                            c[a + '_fed'] += bool(t.get('fed_today'))
                            c[a + '_cared'] += bool(t.get('cared_today'))
                            c[a + '_held'] += t.get('yield_units', 0)
                            if a == 'GOOSE':
                                geese_pos.append((x, y))
                        elif t.get('kind') in ('COOP', 'PASTURE'):
                            c['empty_' + t['kind']] += 1
            inv_egg = sum(inv.get('EGG', 0) for inv in priv.get('inventories', []) or [])
            days[pid].append(dict(day=day, money=round(farm['money']), hands=len(farm['hands']),
                                  land=list(farm['unlocked_quadrants']), anim=dict(c), geese_pos=geese_pos,
                                  shed_egg=priv['shed'].get('EGG', 0), inv_egg=inv_egg,
                                  egg_px=obs0.market['prices']['EGG'], egg_inv=obs0.market['inventory']['EGG'],
                                  egg_shops=sum(s in EGG_SHOPS for s in shops), nshops=len(shops),
                                  mkt=dict(mk[pid][day])))
        return oeod(state, env, day)

    def rec_agent(seat):
        def agent(obs, cfg=None):
            t = obs['step']
            a = acts[t + 1][seat] if t + 1 < len(acts) else None
            if not isinstance(a, dict):
                a = {"farmer": ["PASS"], "hands": [], "market": []}
            return a
        return agent

    K._commit_unit = commit; K._process_market = pm; K._end_of_day = eod
    t0 = time.time()
    try:
        r = lean.play(None, None, seed, agent_objs=[rec_agent(0), rec_agent(1)])
    finally:
        K._commit_unit = oc; K._process_market = opm; K._end_of_day = oeod
    return dict(gid=g['id'], teams=g['info']['TeamNames'], rec=g['rewards'], rep=r['r'], days=days,
                wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    gpath, rpath, out = sys.argv[1:4]
    refs = [json.loads(l) for l in open(rpath, encoding='utf-8')]
    gids = {r['gid'] for r in refs}
    games = []
    with gzip.open(gpath, 'rt', encoding='utf-8') as f:
        for l in f:
            g = json.loads(l)
            if g['id'] in gids:
                games.append(g)
    print(len(games), 'games', flush=True)
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fo:
        for res in ex.map(_play, games, chunksize=2):
            fo.write(json.dumps(res, ensure_ascii=False) + '\n'); fo.flush()
