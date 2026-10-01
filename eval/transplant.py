"""Repaired open-loop replay of an elite route ("transplant"), driven by the recording's OUTCOMES.

The reference replay records, per step, which market orders of the elite seat actually succeeded (hires, land,
seed/animal/product purchases, sales). The transplant issues exactly those, so requests the recording could not
afford are not retried. Repairs on top:
  R0 hand actions padded / truncated to the live hand count; hires kept in their original queue position.
  R1 day-0 hire reservation: if the recording reached the day-1 hires with less than `slack_min` dollars to spare,
     one unit of the cheapest seed bought late on day 0 is dropped, so fill-price drift cannot starve those hires.
  R2 plant trim: surplus PLANT requests (more than seeds on hand) become PASS instead of the engine dropping all.
  R3 emergency sells: before a step whose fixed-price purchases (HIRE / LAND / SEED / ANIMAL) would run short of
     cash, SELL shed goods worth the deficit (wheat last).
usage (test): transplant.py games.jsonl.gz cand.py results.jsonl [max] [slack_min] [filter]
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kaggle_environments.envs.kaggriculture import kaggriculture as K

SEED_PRICE = {c: K.CROPS[c]['seed'] for c in K.CROPS}
ANIMAL_PRICE = {a: K.ANIMALS[a]['cost'] for a in K.ANIMALS}
FIXED = ('HIRE', 'BUY_LAND', 'BUY_SEED', 'BUY_ANIMAL')


def _fib_cost(n_hires, already=0):
    return sum(K._hire_cost(already + i) for i in range(n_hires))


def reference_log(d, seat):
    """Replay the recording. Returns per-step snapshots of `seat` (hands, money), the successful market outcomes per
    step, the shop list and the reproduction flag."""
    import lean, pinned4
    from diag_collapse import snap_tape
    log = []
    outcomes = collections.defaultdict(list)   # step -> [(op, item, qty)] in commit order (aggregated per order)
    STEP = [0]; FARMS = [None, None]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[seat] is not None and farm is FARMS[seat]:
            lst = outcomes[STEP[0]]
            if lst and lst[-1][0] == op and lst[-1][1] == item:
                lst[-1][2] += 1
            else:
                lst.append([op, item, 1])
        return ok
    oh = K._do_hire
    def hire(farm, private, bs, mult=1):
        m0 = farm['money']; oh(farm, private, bs, mult)
        if FARMS[seat] is not None and farm is FARMS[seat] and farm['money'] != m0:
            outcomes[STEP[0]].append(['HIRE', None, 1])
    ol = K._do_buy_land
    def land(farm, bs):
        m0 = farm['money']; ol(farm, bs)
        if FARMS[seat] is not None and farm is FARMS[seat] and farm['money'] != m0:
            outcomes[STEP[0]].append(['BUY_LAND', None, 1])
    opm = K._process_market
    def pm(state, env):
        STEP[0] = state[0].observation.step
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        return opm(state, env)
    K._commit_unit = commit; K._do_hire = hire; K._do_buy_land = land; K._process_market = pm
    try:
        ag = [pinned4._tape(d['acts'], 0), pinned4._tape(d['acts'], 1)]
        ag[seat] = snap_tape(d['acts'], seat, log)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._commit_unit = oc; K._do_hire = oh; K._do_buy_land = ol; K._process_market = opm
    hands = [x['hands'] for x in log] + [0]
    money = [x['money'] for x in log] + [0]
    ok = [int(x) for x in r['r']] == [int(x) for x in d['rewards']]
    return dict(hands=hands, money=money, outcomes=dict(outcomes), shops=list(r['shops']), ok=ok)


def _orders_from_outcomes(lst):
    out = []
    for op, item, q in lst:
        if op in ('HIRE', 'BUY_LAND'):
            out.extend([[op]] * q)
        else:
            out.append([op, item, q])
    return out


def build_agent(acts, seat, ref, slack_min=8, emergency=False, plant_trim=True):
    hands_rec, money_rec, outcomes = ref['hands'], ref['money'], ref['outcomes']
    orders = {t: _orders_from_outcomes(lst) for t, lst in outcomes.items()}
    # R1': day-0 hire reservation, armed only when the recording reached its day-1 hires with a thin margin and
    # fired only once live cash is observed below the recorded trajectory; drops one unit of a feed-safe seed
    # (melon, tomato, carrot, strawberry; wheat last) from the latest remaining day-0 seed purchase.
    need_d1 = _fib_cost(hands_rec[25] if len(hands_rec) > 25 else 0)
    slack = (money_rec[23] if len(money_rec) > 23 else 0) - need_d1
    r1 = {'armed': need_d1 > 0 and slack < slack_min, 'done': False, 'slack': slack}
    PREF = {'MELON': 0, 'TOMATO': 1, 'CARROT': 2, 'STRAWBERRY': 3, 'WHEAT': 4}

    def _r1_check(t, live_money):
        if not r1['armed'] or r1['done'] or t > 23:
            return
        drift = money_rec[t] - live_money
        if drift <= max(0.0, r1['slack']):
            return
        best = None
        for t2 in range(23, t, -1):
            for j, o in enumerate(orders.get(t2, [])):
                if o[0] == 'BUY_SEED' and o[2] > 0:
                    key = (PREF.get(o[1], 9), -t2)
                    if best is None or key < best[0]:
                        best = (key, t2, j)
        if best is None:
            return
        _, t2, j = best
        o = orders[t2][j]; o[2] -= 1
        if o[2] <= 0:
            orders[t2].pop(j)
        r1['done'] = True

    def agent(obs, cfg=None):
        t = obs['step']
        a = acts[t + 1][seat] if t + 1 < len(acts) else None
        if not isinstance(a, dict):
            a = {"farmer": ["PASS"], "hands": [], "market": []}
        farm = obs['farms'][obs['player']]
        priv = obs['private']
        _r1_check(t, float(farm['money']))
        live_hands = farm.get('hands') or []
        farmer = a.get('farmer') or ['PASS']
        hands = list(a.get('hands') or [])
        hands = (hands + [['PASS']] * len(live_hands))[:len(live_hands)]
        if plant_trim:
            seeds = priv.get('seeds') or {}
            units = [farmer] + hands
            demand = collections.Counter(u[1] for u in units if isinstance(u, list) and len(u) >= 2 and u[0] == 'PLANT')
            for crop, n in demand.items():
                have = int(seeds.get(crop, 0))
                if n > have:
                    surplus = n - have
                    for i in range(len(units) - 1, -1, -1):
                        u = units[i]
                        if surplus and isinstance(u, list) and len(u) >= 2 and u[0] == 'PLANT' and u[1] == crop:
                            units[i] = ['PASS']; surplus -= 1
                    farmer, hands = units[0], units[1:]
        market = [list(o) for o in orders.get(t, [])]
        if emergency and market:
            money = float(farm['money']); hires_today = int(farm.get('hires_today', 0))
            unlocked = len(farm.get('unlocked_quadrants') or ['NW'])
            prices = obs['market']['prices']
            shed = {k: int(v) for k, v in (priv.get('shed') or {}).items()}
            need = 0.0; m = money
            for o in market:
                op = o[0]; cost = 0.0
                if op == 'HIRE':
                    cost = K._hire_cost(hires_today); hires_today += 1
                elif op == 'BUY_LAND':
                    k = unlocked - 1
                    cost = K.LAND_PRICES[k] if 0 <= k < len(K.LAND_PRICES) else 0; unlocked += 1
                elif op == 'BUY_SEED':
                    cost = SEED_PRICE.get(o[1], 0) * int(o[2])
                elif op == 'BUY_ANIMAL':
                    cost = ANIMAL_PRICE.get(o[1], 0) * int(o[2])
                elif op == 'BUY_PRODUCT':
                    m -= (float(prices.get(o[1], 0)) + 2) * int(o[2]); continue
                elif op == 'SELL':
                    q = min(int(o[2]), shed.get(o[1], 0)); m += float(prices.get(o[1], 0)) * q * 0.9
                    shed[o[1]] = shed.get(o[1], 0) - q; continue
                if cost > m:
                    need = max(need, cost - m)
                m -= cost
            if need > 0:
                extra = []; target = need * 1.1
                for item, n in sorted(shed.items(), key=lambda kv: (kv[0] == 'WHEAT', -float(prices.get(kv[0], 0)) * kv[1])):
                    if target <= 0 or item not in K.PRODUCTS or n <= 0: continue
                    p = float(prices.get(item, 0)) * 0.9
                    if p <= 0: continue
                    q = min(int(n), int(target / p) + 1)
                    extra.append(['SELL', item, q]); target -= q * p
                if extra and len(extra) + len(market) <= 10:
                    market = extra + market
        return {"farmer": farmer, "hands": hands, "market": market[:10]}
    return agent


def transplant_play(d, seat, cand, ref, slack_min=8, **kw):
    import lean
    from eval_elite_routes import install_town
    orig = install_town(ref['shops'])
    try:
        ag = [None, None]
        ag[seat] = build_agent(d['acts'], seat, ref, slack_min=slack_min, **kw)
        ag[1 - seat] = lean.load(cand)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig
    return r


if __name__ == '__main__':
    from eval_elite_routes import load_games
    path, cand, res = sys.argv[1], sys.argv[2], sys.argv[3]
    maxn = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    slack_min = int(sys.argv[5]) if len(sys.argv) > 5 else 8
    flt = sys.argv[6] if len(sys.argv) > 6 else 'collapse'
    rows = [json.loads(l) for l in open(res)]
    pick = [r for r in rows if r['m'] is not None and (r['tape'] < 0.6 * r['rec_tape'] if flt == 'collapse' else r['team'] == flt)]
    byt = collections.defaultdict(list)
    for r in pick: byt[r['team']].append(r)
    sel = []
    while len(sel) < maxn and any(byt.values()):
        for t in list(byt):
            if byt[t] and len(sel) < maxn: sel.append(byt[t].pop(0))
    games = {g['id']: g for g in load_games(path)}
    tot = collections.Counter()
    for r in sel:
        d = games[r['gid']]; s = r['seat']
        ref = reference_log(d, s)
        out = transplant_play(d, s, cand, ref, slack_min=slack_min)
        tape, cd = out['r'][s], out['r'][1 - s]
        ratio = tape / r['rec_tape'] if tape is not None else 0
        tot['n'] += 1; tot['ratio'] += ratio; tot['win'] += (tape or 0) > (cd or 0); tot['m'] += (tape or 0) - (cd or 0)
        print(f"{r['team'][:14]:14s} s{s} gid {r['gid']} rec {r['rec_tape']:7.0f} | plain {r['tape']:7.0f} ({r['tape']/r['rec_tape']:.2f}) | repaired {tape:7.0f} ({ratio:.2f}) vs v100 {cd:7.0f} m {tape-cd:+7.0f} err {out['err']}")
    n = max(1, tot['n'])
    print(f"repaired: mean ratio {tot['ratio']/n:.2f}, wins vs cand {tot['win']}/{tot['n']}, mean margin {tot['m']/n:+.0f}")
