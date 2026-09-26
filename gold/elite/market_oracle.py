"""Market oracle: how much revenue an optimal sell schedule would have earned on the goods our agent actually produced,
against the rival's actual sales and the town's actual drain (pinned replay, rival fixed).

For each pinned game: replay (our recorded prefix to S, then the candidate) and capture, per step and product, our shed,
our sales (units, revenue), the rival's sales (units), and the market inventory at market time. Then, per product, a
dynamic programme over steps chooses how many units to sell each step to maximise revenue on the same arrivals, pricing
each unit on the exact engine curve at the exogenous inventory (observed minus our own cumulative sales) plus the units
we sell before it. Two bounds: unconstrained holding, and holding at most `cap` units of the product at any time.
usage: market_oracle.py games.json S cand.py out.jsonl [maxgames] [cap]"""
import sys, os, json, time, collections
import numpy as np
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, '/home/user/kaggriculture/arena'); sys.path.insert(0, '/home/user/kaggriculture/gold/harness')
PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]


def dp_revenue(arrivals, rival, exo_inv, price_tab, base_i, t0, hold_cap=None, x_max=250):
    """arrivals[t], rival[t], exo_inv[t] for t in 0..718 (exo_inv = inventory at market time minus our cumulative sales).
    Returns the optimal revenue from step t0 on, given stock at t0 = sum(arrivals[:t0+1]) - our sales before t0 (caller
    folds that into arrivals[t0])."""
    T = 719
    A = np.cumsum(arrivals)                      # cumulative NET arrivals by t (withdrawals for feed/fertilizer count negative)
    Amin = np.minimum.accumulate(A[::-1])[::-1]  # cumulative sales up to t may never exceed the stock still there later
    U = int(max(0.0, A.max()))
    if U <= 0:
        return 0.0, []
    NEG = -1e18
    V_next = np.zeros(U + 1)                     # V(719, c) = 0 (unsold units are worthless)
    # after the last processed step nothing sells: V at t=718 computed in the loop
    choice = {}
    for t in range(T - 1, t0 - 1, -1):
        stock_max = int(max(0.0, Amin[t]))      # c + x <= min future cumulative stock (units later withdrawn stay)
        c = np.arange(U + 1)
        avail = np.maximum(0, np.minimum(stock_max, U) - c)   # sellable units at t for cumulative sold c
        if hold_cap is not None:
            # holding more than hold_cap is infeasible: states with avail > hold_cap must sell down this step
            pass
        # price of the j-th unit we sell at t: price(exo + c + rival_half + j)
        base = exo_inv[t] + 0.5 * rival[t]
        V_t = np.full(U + 1, NEG)
        best_x = np.zeros(U + 1, dtype=np.int32)
        # x = 0
        ok0 = (avail >= 0)
        if hold_cap is not None:
            ok0 = avail <= hold_cap
        V_t = np.where(ok0, V_next, NEG)
        xmax_here = min(x_max, stock_max)
        for x in range(1, xmax_here + 1):
            # revenue of selling x units starting at inventory base + c
            idx = (base + c - base_i).astype(np.int64)
            idx0 = np.clip(idx, 0, len(price_tab) - 1 - x)
            rev = price_tab_cum[idx0 + x] - price_tab_cum[idx0]
            feas = avail >= x
            if hold_cap is not None:
                feas &= (avail - x) <= hold_cap
            cand = np.where(feas, rev + np.concatenate([V_next[x:], np.full(x, NEG)]), NEG)
            better = cand > V_t
            V_t = np.where(better, cand, V_t); best_x = np.where(better, x, best_x)
        choice[t] = best_x
        V_next = V_t
    # V at t0 with c = 0; also the plan (x_t) reached from c = 0
    plan = np.zeros(T); c = 0
    for t in range(t0, T):
        x = int(choice[t][c]) if t in choice else 0
        plan[t] = x; c += x
    return float(V_next[0]), plan


def eval_plan(plan, rival, exo_inv, price_tab, base_i):
    rev = 0.0; c = 0
    for t in range(len(plan)):
        x = int(plan[t])
        if x <= 0:
            continue
        base = exo_inv[t] + 0.5 * rival[t] + c
        idx0 = int(np.clip(base - base_i, 0, len(price_tab) - 1 - x))
        rev += float(price_tab_cum[idx0 + x] - price_tab_cum[idx0]); c += x
    return rev


def job(t):
    import lean, pinned4
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    path, idx, team, cand, S, hold_cap = t
    d = json.load(open(path, encoding='utf-8'))[idx]
    names = d['info']['TeamNames']; P = names.index(team); O = 1 - P
    spawns, shops, rref = pinned4.reference(d)
    orig = pinned4.install_pinned(S // 24, O, spawns, shops)
    T = 719
    our_sales_u = {p: np.zeros(T) for p in PRODUCTS}; our_sales_r = {p: np.zeros(T) for p in PRODUCTS}
    riv_sales = {p: np.zeros(T) for p in PRODUCTS}
    our_buys = {p: np.zeros(T) for p in PRODUCTS}
    inv_at = {p: np.zeros(T) for p in PRODUCTS}; shed_at = {p: np.zeros(T) for p in PRODUCTS}
    FARMS = [None, None]; STEP = [0]
    oc = K._commit_unit
    def commit(op, item, price, farm, private, market, cap=100):
        ok = oc(op, item, price, farm, private, market, cap)
        if ok and FARMS[0] is not None and item in PRODUCTS:
            i = 0 if farm is FARMS[0] else 1; s = STEP[0]
            if op == 'SELL':
                if i == P: our_sales_u[item][s] += 1; our_sales_r[item][s] += price
                else: riv_sales[item][s] += 1
            elif op == 'BUY_PRODUCT' and i == P:
                our_buys[item][s] += 1
        return ok
    opm = K._process_market
    def pm(state, env):
        s = state[0].observation.step; STEP[0] = s
        FARMS[0], FARMS[1] = state[0].observation.farms[0], state[0].observation.farms[1]
        if s < T:
            m = state[0].observation.market['inventory']; sh = state[P].observation.private['shed']
            for p in PRODUCTS:
                inv_at[p][s] = int(m[p]); shed_at[p][s] = int(sh.get(p, 0))
        return opm(state, env)
    K._commit_unit = commit; K._process_market = pm
    try:
        A = lean.load(cand)
        ag = [None, None]; ag[P] = pinned4._prefixed(A, d['acts'], P, S); ag[O] = pinned4._tape(d['acts'], O)
        r = lean.play(None, None, d['info']['seed'], agent_objs=ag)
    finally:
        K._end_of_day = orig; K._commit_unit = oc; K._process_market = opm
    out = dict(gid=d['id'], opp=names[O], cand=cand, S=S, us=r['r'][P], them=r['r'][O], m=(r['r'][P] - r['r'][O]) if r['r'][P] is not None else None,
               realized={}, oracle={}, oracle_cap={}, units={})
    global price_tab_cum
    for p in PRODUCTS:
        # arrivals: shed_t - shed_{t-1} + sold_{t-1} - bought_{t-1}
        arr = np.zeros(T)
        for s in range(1, T):
            arr[s] = shed_at[p][s] - shed_at[p][s - 1] + our_sales_u[p][s - 1] - our_buys[p][s - 1]   # net: pickups negative
        arr[0] = shed_at[p][0]
        # only the controller phase decides from S on: fold the stock held at S into arrivals[S], keep earlier sales as realized
        stock_S = shed_at[p][S]
        arr2 = np.zeros(T); arr2[S] = stock_S; arr2[S + 1:] = arr[S + 1:]
        cum_ours = np.cumsum(our_sales_u[p])
        before = np.concatenate([[0.0], cum_ours[:-1]])            # our cumulative sales before step t
        # exogenous inventory from S on: observed inventory minus only the sales the candidate made from S onward
        exo = inv_at[p] - np.maximum(0.0, before - (cum_ours[S - 1] if S > 0 else 0.0))
        # price table over a wide inventory range
        lo = int(min(exo[S:].min(), 10000) - 1500); hi = int(max(exo[S:].max(), 10000) + 2500)
        tab = np.array([K.market_price(p, i) for i in range(lo, hi + 1)], dtype=np.float64)
        price_tab_cum = np.concatenate([[0.0], np.cumsum(tab)])
        realized = float(our_sales_r[p][S:].sum())
        units = float(arr2.sum())
        best, _ = dp_revenue(arr2, riv_sales[p], exo, tab, lo, S, None)
        out['realized'][p] = realized; out['oracle'][p] = best; out['units'][p] = float(np.maximum(0, arr2).sum())
        for capv in (20, 10, 5):
            bc, _ = dp_revenue(arr2, riv_sales[p], exo, tab, lo, S, capv)
            out.setdefault('oracle_cap%d' % capv, {})[p] = bc
        out['oracle_cap'][p] = out['oracle_cap20'][p]
        # forecast plan: the rival's sales and the exogenous inventory path predicted from the previous day's pattern
        riv_fc = np.zeros(T); riv_fc[S + 24:] = riv_sales[p][S:T - 24]
        # exogenous inventory forecast: drift of the last 24 steps extrapolated (drain net of rival supply), capped
        exo_fc = exo.copy()
        for t in range(S + 24, T):
            exo_fc[t] = exo[S + 23] + (exo[S + 23] - exo[S]) / 23.0 * (t - S - 23)
        for capv in (10, 5):
            _, plan = dp_revenue(arr2, riv_fc, exo_fc, tab, lo, S, capv)
            out.setdefault('plan_cap%d' % capv, {})[p] = eval_plan(plan, riv_sales[p], exo, tab, lo)
    return out


if __name__ == '__main__':
    path, S, cand, out = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    maxg = int(sys.argv[5]) if len(sys.argv) > 5 else 12
    hold_cap = int(sys.argv[6]) if len(sys.argv) > 6 else 40
    team = 'offhand'
    games = [(path, i) for i, d in enumerate(json.load(open(path, encoding='utf-8'))) if team in d['info']['TeamNames']][:maxg]
    jobs = [(f, i, team, cand, S, hold_cap) for f, i in games]
    t0 = time.time(); res = []
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '4'))) as ex, open(out, 'w') as fh:
        for r in ex.map(job, jobs):
            res.append(r); fh.write(json.dumps(r) + '\n'); fh.flush()
    print(f"{len(res)} games, cand {cand}, S {S}, hold cap {hold_cap}, wall {time.time()-t0:.0f}s")
    print(f"{'product':11s} {'units':>6} {'realized':>9} {'unconstr':>9} {'cap20':>8} {'cap10':>8} {'cap5':>8}   (gains vs realized)")
    tots = collections.Counter()
    for p in PRODUCTS:
        u = np.mean([r['units'][p] for r in res]); rr = np.mean([r['realized'][p] for r in res])
        oo = np.mean([r['oracle'][p] for r in res]); c20 = np.mean([r['oracle_cap20'][p] for r in res]); c10 = np.mean([r['oracle_cap10'][p] for r in res]); c5 = np.mean([r['oracle_cap5'][p] for r in res])
        tots['r'] += rr; tots['o'] += oo; tots['20'] += c20; tots['10'] += c10; tots['5'] += c5
        print(f"{p:11s} {u:6.0f} {rr:9.0f} {oo-rr:+9.0f} {c20-rr:+8.0f} {c10-rr:+8.0f} {c5-rr:+8.0f}")
    print(f"{'TOTAL':11s} {'':6s} {tots['r']:9.0f} {tots['o']-tots['r']:+9.0f} {tots['20']-tots['r']:+8.0f} {tots['10']-tots['r']:+8.0f} {tots['5']-tots['r']:+8.0f}")
    print("per game gain (cap 10):", ' '.join(f"{sum(r['oracle_cap10'].values())-sum(r['realized'].values()):+.0f}" for r in res))
    print(f"\nforecast plan (rival = yesterday's pattern, inventory drift extrapolated), evaluated on the true path:")
    for capv in (10, 5):
        g = {p: np.mean([r['plan_cap%d' % capv][p] - r['realized'][p] for r in res]) for p in PRODUCTS}
        print(f"  cap {capv:2d}: total {sum(g.values()):+7.0f}  " + ' '.join(f"{p[:5]} {g[p]:+6.0f}" for p in PRODUCTS))
