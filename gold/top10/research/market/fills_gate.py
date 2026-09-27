"""Market fills on an elite gate: every fill of both farms by step, the book after every step, day-end farm census.
usage: fills_gate.py games.jsonl.gz refs.jsonl cand.py out.jsonl [max] [gid_list_file]
Row: gid, seat, team, m, us, tape, inv[t] (inventory - I0 per product after step t's market + town drain),
fills: [[t, side, op, item, n, dollars]] side 0 = us (candidate), 1 = elite; op S/B (sell / buy product),
census[day][side] = {crop/animal: count, 'hands': n, 'money': $}, disc[day][side] = {item: units discarded at night}.
NPROC workers (default 2)."""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')

P = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]


def _play(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig = install_town(ref['shops'])
    ctx = {'farms': None, 'priv': None, 'step': 0}
    fills = collections.defaultdict(lambda: [0, 0])
    inv = []
    census = []
    disc = collections.defaultdict(lambda: collections.Counter())

    def side_of_farm(farm):  # 0 = us, 1 = elite
        i = 0 if farm is ctx['farms'][0] else 1
        return 0 if i == 1 - s else 1

    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and ctx['farms'] is not None and op in ('SELL', 'BUY_PRODUCT'):
            k = (ctx['step'], side_of_farm(farm), 'S' if op == 'SELL' else 'B', item)
            f = fills[k]; f[0] += 1; f[1] += price
        return ok
    opm = K._process_market
    def pm(state, env):
        ctx['farms'] = state[0].observation.farms
        ctx['priv'] = [state[0].observation.private, state[1].observation.private]
        ctx['step'] = int(state[0].observation.step)
        return opm(state, env)
    otc = K._town_consume
    def tc(env, state, step):
        r = otc(env, state, step)
        m = state[0].observation.market
        inv.append([int(m['inventory'][p]) - 10000 for p in P])
        return r
    odr = K._drop_inventories_to_shed
    def drop(private, cap):
        before = collections.Counter()
        for iv in private['inventories']:
            for k, n in iv.items():
                if n > 0: before[k] += n
        sh0 = dict(private['shed'])
        r = odr(private, cap)
        pr = ctx['priv']
        if pr is not None:
            i = 0 if private is pr[0] else 1
            sd = 0 if i == 1 - s else 1
            day = ctx['step'] // 24
            for k, n in before.items():
                got = private['shed'].get(k, 0) - sh0.get(k, 0)
                if n - got > 0: disc[(day, sd)][k] += n - got
        return r
    oeod = K._end_of_day  # install_town's version
    def eod(state, env, day):
        farms = state[0].observation.farms
        row = [None, None]
        for i, farm in enumerate(farms):
            c = collections.Counter()
            for yrow in farm['tiles']:
                for tl in yrow:
                    if isinstance(tl, dict):
                        if tl.get('kind') == 'PLANT': c[tl.get('crop', tl.get('type', '?'))] += 1
                        elif 'animal' in tl: c[tl['animal']] += 1
                        else: c[tl.get('kind', '?')] += 1
            c['hands'] = len(farm.get('hands') or [])
            c['money'] = round(float(farm['money']))
            c['quads'] = len(farm.get('unlocked_quadrants') or [])
            row[0 if i == 1 - s else 1] = dict(c)
        census.append(row)
        return oeod(state, env, day)
    K._commit_unit = commit; K._process_market = pm; K._town_consume = tc; K._drop_inventories_to_shed = drop
    K._end_of_day = eod
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm; K._town_consume = otc; K._drop_inventories_to_shed = odr
    tape, cd = r['r'][s], r['r'][1 - s]
    fl = [[k[0], k[1], k[2], k[3], v[0], v[1]] for k, v in sorted(fills.items())]
    dd = [[k[0], k[1], dict(v)] for k, v in sorted(disc.items())]
    return dict(gid=ref['gid'], seat=s, team=ref['team'], cand=cand, tape=tape, us=cd,
                m=(cd - tape) if tape is not None and cd is not None else None, err=r['err'], shops=ref['shops'],
                inv=inv, fills=fl, census=census, disc=dd, wall=round(time.time() - t0, 1))


if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, refs, cand, out = sys.argv[1:5]
    maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 6
    ids = set(int(x) for x in open(sys.argv[6]).read().split()) if len(sys.argv) > 6 else None
    R = [json.loads(l) for l in open(refs, encoding='utf-8')]
    if ids: R = [r for r in R if r['gid'] in ids]
    R = R[:maxg]
    need = {r['gid'] for r in R}
    games = {g['id']: g for g in load_games(path) if g['id'] in need}
    jobs = [(games[r['gid']], r, cand) for r in R]
    t0 = time.time(); n = 0
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '2'))) as ex, open(out, 'w', encoding='utf-8') as fh:
        for x in ex.map(_play, jobs):
            n += 1; fh.write(json.dumps(x, ensure_ascii=False) + '\n'); fh.flush()
            print(n, x['gid'], x['team'], x['m'], x['wall'], flush=True)
    print('done', n, round(time.time() - t0), 's')
