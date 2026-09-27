"""Per-day schedule of a candidate and a repaired elite in the elite's town (same set-up as elite_gate._play).
usage: day_sched.py cand.py team [n] [out.jsonl]      # prints the team mean per day, writes per-seat records
"""
import sys, os, json, time, collections
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness'); sys.path.insert(0, '/home/user/kaggriculture/gold/elite')
Q = lambda x, y: ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')

def _play(t):
    import lean
    from eval_elite_routes import install_town
    from transplant import build_agent
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    d, ref, cand = t
    s = ref['seat']
    rr = dict(hands=ref['hands'], money=ref['money'], outcomes={int(k): v for k, v in ref['outcomes'].items()}, shops=ref['shops'])
    orig_eod = K._end_of_day  # original (unpinned) end of day
    town_eod = install_town(ref['shops'])  # returns the original; K._end_of_day is now the pinned one
    pinned_eod = K._end_of_day
    days = [[], []]  # per farm: list of per-day dicts
    sold = [collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)]
    FARMS = [None, None]; DAY = [0]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None:
            i = 0 if farm is FARMS[0] else 1
            if op == 'SELL': sold[i][DAY[0]]['u_' + item] += 1; sold[i][DAY[0]]['$_' + item] += price
            elif op == 'BUY_PRODUCT': sold[i][DAY[0]]['buy_' + item] += 1
            elif op == 'BUY_SEED': sold[i][DAY[0]]['seed_' + item] += 1
            elif op == 'BUY_ANIMAL': sold[i][DAY[0]]['anim_' + item] += 1
        return ok
    opm = K._process_market
    def pm(state, env):
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        DAY[0] = int(K.get(state[0].observation, 'step', 0)) // 24
        return opm(state, env)
    def eod(state, env, day):
        obs0 = state[0].observation
        for pid, farm in enumerate(obs0.farms):
            private = state[pid].observation.private
            c = collections.Counter(); planted = collections.Counter(); ripe = collections.Counter()
            for y, row in enumerate(farm['tiles']):
                for x, tile in enumerate(row):
                    if isinstance(tile, dict):
                        if tile.get('crop'):
                            c[tile['crop']] += 1
                            if tile.get('planted_day') == day: planted[tile['crop'] + '@' + Q(x, y)] += 1
                            ripe[tile['crop']] += tile.get('yield_units', 0)
                        elif tile.get('animal'):
                            c[tile['animal']] += 1; ripe[tile['animal']] += tile.get('yield_units', 0)
                        elif tile.get('kind') == 'WEED': c['WEED'] += 1
                        else: c['empty_' + str(tile.get('kind'))] += 1
                    elif tile is None: c['free'] += 1
            days[pid].append(dict(day=day, money=round(farm['money']), hands=len(farm['hands']), land=list(farm['unlocked_quadrants']),
                                  tiles=dict(c), planted=dict(planted), ripe=dict(ripe), shed={k: v for k, v in private['shed'].items() if v},
                                  seeds={k: v for k, v in private['seeds'].items() if v}, mkt=dict(sold[pid][day])))
        return pinned_eod(state, env, day)
    K._commit_unit = commit; K._process_market = pm; K._end_of_day = eod
    t0 = time.time()
    try:
        ag = [None, None]; ag[s] = build_agent(d['acts'], s, rr, slack_min=20); A = lean.load(cand); ag[1 - s] = A
        r = lean.play(None, None, ref['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig_eod; K._commit_unit = oc; K._process_market = opm
    return dict(gid=ref['gid'], seat=s, team=ref['team'], shops=ref['shops'], elite=r['r'][s], us=r['r'][1 - s], err=r['err'],
                days_elite=days[s], days_us=days[1 - s], wall=round(time.time() - t0, 1))

if __name__ == '__main__':
    from eval_elite_routes import load_games
    cand, team = sys.argv[1], sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    out = sys.argv[4] if len(sys.argv) > 4 else None
    R = [json.loads(l) for l in open('gold/elite/elite_gate_refs.jsonl', encoding='utf-8')]
    R = [r for r in R if team == 'ALL' or r['team'] == team][:n]
    games = {g['id']: g for g in load_games('moon/elite/games_2026-09-20.jsonl.gz') if g['id'] in {r['gid'] for r in R}}
    jobs = [(games[r['gid']], r, cand) for r in R]
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex:
        res = list(ex.map(_play, jobs))
    if out:
        with open(out, 'w') as fh:
            for x in res: fh.write(json.dumps(x) + '\n')
    for x in res:
        print('seat', x['gid'], x['seat'], x['team'], 'elite', x['elite'], 'us', x['us'], 'shops', x['shops'][:5], x['err'])
    for who in ('elite', 'us'):
        print('==== %s (mean over %d seats)' % (who, len(res)))
        print('day  money  hands land  planted(crop@quadrant)                                  sold units                         tiles')
        for day in range(30):
            recs = [x['days_' + who][day] for x in res if len(x['days_' + who]) > day]
            if not recs: continue
            k = len(recs)
            pl = collections.Counter(); so = collections.Counter(); ti = collections.Counter()
            for rc in recs:
                pl.update(rc['planted']); ti.update(rc['tiles'])
                for kk, v in rc['mkt'].items():
                    if kk.startswith('u_') or kk.startswith('anim_') or kk.startswith('buy_'): so[kk] += v
            land = sum(len(rc['land']) for rc in recs) / k
            fmt = lambda cnt, keys=None: ' '.join('%s:%.1f' % (kk[:6] + kk[6:].replace('@', '@'), v / k) for kk, v in sorted(cnt.items(), key=lambda kv: -kv[1]) if v / k >= 0.3)
            print('%3d %7.0f %5.1f %4.1f  %-55s %-35s %s' % (day, sum(rc['money'] for rc in recs) / k, sum(rc['hands'] for rc in recs) / k, land,
                  fmt(pl)[:55], fmt(so)[:35], ' '.join('%s:%.0f' % (kk[:4], v / k) for kk, v in sorted(ti.items(), key=lambda kv: -kv[1]) if v / k >= 1 and kk != 'free')[:60]))
