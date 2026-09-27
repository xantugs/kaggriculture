"""elite_gate._play + per-day animal/egg stats of both farms.
usage: egg_gate.py games.jsonl.gz refs.jsonl cand.py out.jsonl
Rows: elite_gate row + days_us / days_elite (per day: geese, coops, cows, sheep, fed/cared, egg sales, buys, money)."""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
EGG_SHOPS = ('BAKERY', 'BRUNCH_SPOT')


def _play(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    pinned = K._end_of_day
    led = [collections.Counter(), collections.Counter()]; FARMS = [None, None]; DAY = [0]
    mk = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    days = [[], []]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            dd = mk[i][DAY[0]]
            if op == 'SELL': led[i][item] += price; dd['u_' + item] += 1; dd['$_' + item] += price
            elif op == 'BUY_PRODUCT': led[i][item] -= price; dd['buy_' + item] += 1
            elif op == 'BUY_SEED': led[i]['seed'] -= price
            elif op == 'BUY_ANIMAL': led[i]['anim'] -= price; dd['anim_' + item] += 1
        return ok
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        DAY[0] = int(K.get(state[0].observation, 'step', 0)) // 24
        return opm(state, env)
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[0] is not None: led[0 if farm is FARMS[0] else 1]['hire'] += farm['money'] - m0
    def eod(state, env, day):
        obs0 = state[0].observation
        shops = list(obs0.town.get('unlocked_shops', []))
        for pid, farm in enumerate(obs0.farms):
            priv = state[pid].observation.private
            c = collections.Counter()
            for y, row in enumerate(farm['tiles']):
                for x, tl in enumerate(row):
                    if isinstance(tl, dict):
                        if tl.get('animal'):
                            a = tl['animal']; c[a] += 1
                            c[a + '_fed'] += bool(tl.get('fed_today')); c[a + '_cared'] += bool(tl.get('cared_today'))
                            c[a + '_held'] += tl.get('yield_units', 0)
                        elif tl.get('kind') in ('COOP', 'PASTURE'):
                            c['empty_' + tl['kind']] += 1
                        elif tl.get('crop'):
                            c['crop_' + tl['crop']] += 1
                    elif tl is None:
                        c['free'] += 1
            days[pid].append(dict(day=day, money=round(farm['money']), hands=len(farm['hands']), land=len(farm['unlocked_quadrants']),
                                  anim=dict(c), shed_egg=priv['shed'].get('EGG', 0), egg_px=obs0.market['prices']['EGG'],
                                  egg_shops=sum(x in EGG_SHOPS for x in shops), mkt=dict(mk[pid][day])))
        return pinned(state, env, day)
    K._commit_unit = commit; K._process_market = pm; K._do_hire = hire; K._end_of_day = eod
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._do_hire = oh
    tape, cd = r['r'][s], r['r'][1 - s]
    G = getattr(A, '__globals__', {}) or {}
    rep = {}
    for nm in ('_HD2_REPORT', '_V9_HERD_REPORT', '_Y_REPORT', '_CS_REPORT', '_V231_REPORT', '_GC_REPORT'):
        v = G.get(nm)
        if isinstance(v, dict):
            rep[nm] = {k: vv for k, vv in v.items() if isinstance(vv, (int, float, str)) and vv not in (0, '')}
    try:
        impl = G.get('_IMPL')
        nat = impl.chassis.players.get(1 - s) if impl is not None else None
        if nat and nat.get('route') in impl.chassis.routes:
            tp = impl.chassis.routes[nat['route']]
            plan = collections.Counter()
            for t_, a_ in enumerate(tp[:400]):
                for o in (a_.get('market') or []) if isinstance(a_, dict) else []:
                    if o and o[0] == 'BUY_ANIMAL' and len(o) >= 3:
                        plan['%s%d' % (o[1], t_ // 24)] += int(o[2])
            rep['route'] = str(nat['route']); rep['tape_buys'] = dict(plan)
    except Exception as e:
        rep['route_err'] = repr(e)[:100]
    return dict(rep=rep, gid=ref['gid'], seat=s, team=ref['team'], cand=cand, tape=tape, us=cd, m=(cd - tape) if tape is not None and cd is not None else None,
                err=r['err'], tmax=r['tmax'], wall=round(time.time() - t0, 1), led_us=dict(led[1 - s]), led_elite=dict(led[s]),
                days_us=days[1 - s], days_elite=days[s])


if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, cand, out = sys.argv[1:5]
    R = [json.loads(l) for l in open(refs, encoding='utf-8')]
    gids = {r['gid'] for r in R}
    games = {g['id']: g for g in load_games(path) if g['id'] in gids}
    jobs = [(games[r['gid']], r, cand) for r in R]
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '3'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(_play, jobs):
            fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
