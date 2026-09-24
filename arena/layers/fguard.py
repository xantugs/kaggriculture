# ---------------------------------------------------------------------------
# Local modification (Apache-2.0 notice) by offhand, 2026-09-22.
# FGUARD: the R97 supply guard, for fertilizer.  When the tape's units will pick
# up more fertilizer at the shed next turn than this turn's orders leave in it,
# first trim this turn's fertilizer sale, then top up the fertilizer purchase.
# A short pickup leaves a unit empty-handed and its FERTILIZE a no-op.
# ---------------------------------------------------------------------------
_FG_CFG = _FG_CFG_PLACEHOLDER
_FG_PARENT = agent
_FG_REPORT = {"fg_changes": 0, "fg_units": 0, "fg_trim": 0, "fg_buy": 0, "fg_declines": 0, "fg_errors": 0}


def _fg_supply(obs, action):
    step = int(obs["step"]); player = int(obs["player"]); day = step // 24
    if not _FG_CFG.get("from", 144) <= step < _FG_CFG.get("to", 695):
        return action
    native = _IMPL.chassis.players[player]
    future = _IMPL.chassis.routes[2 if step + 1 >= 648 else native["route"]][step + 1]
    commands = [future.get("farmer") or ["PASS"], *(future.get("hands") or [])]
    if not any(c[:2] == ["PICKUP", "FERTILIZER"] for c in commands):
        return action
    orders = action.get("market") or []
    if len(orders) > 10:
        return action
    farm, private = _PLANNER_NS["_clone_state"](obs["farms"][player], obs["private"])
    for actor, c in enumerate([action.get("farmer") or ["PASS"], *(action.get("hands") or [])][:len(private["inventories"])]):
        _PLANNER_NS["_apply_unit_action"](farm, private, actor, c, 10, day, 24, 100)
    positions = [tuple(farm["farmer"]), *map(tuple, farm["hands"])]
    night = step % 24 == 23
    access = ((4, 4), (5, 4), (4, 5), (5, 5))
    if night:
        positions = [(4, 4)]
    else:
        for order in orders:
            if order and order[0] == "HIRE":
                positions.append(min(access, key=lambda p: (positions.count(p), access.index(p))))
    need = sum(max(0, int(c[2]) if len(c) > 2 else 1) for pos, c in zip(positions, commands)
               if pos in access and c[:2] == ["PICKUP", "FERTILIZER"])
    if not need:
        return action
    stock, buys, _ = _r97_market_stock(private["shed"], orders)
    final, loss = _r97_delivery(stock, private, night)
    if final.get("FERTILIZER", 0) >= need:
        return action
    result = copy.deepcopy(action); proposed = result["market"]
    def project(candidate):
        s, b, sales = _r97_market_stock(private["shed"], candidate)
        f, l = _r97_delivery(s, private, night)
        safe = all(b.get(i, 0) >= q for i, q in buys.items()) and all(q <= loss.get(it, 0) for it, q in l.items())
        return f, sales, safe
    trimmed = 0
    if _FG_CFG.get("trim", True):
        for index in range(len(proposed) - 1, -1, -1):
            if proposed[index][:2] != ["SELL", "FERTILIZER"]:
                continue
            f, sales, safe = project(proposed); shortage = max(0, need - f.get("FERTILIZER", 0))
            if not shortage:
                break
            sold = sales.get(index, 0)
            if not sold:
                continue
            old = proposed[index][2]; proposed[index][2] = max(0, sold - shortage)
            after, _, safe = project(proposed)
            if not safe or after.get("FERTILIZER", 0) <= f.get("FERTILIZER", 0):
                proposed[index][2] = old
            else:
                trimmed += old - proposed[index][2]
    f, _, safe = project(proposed); shortage = max(0, need - f.get("FERTILIZER", 0))
    bought = 0
    if shortage and _FG_CFG.get("buy", True):
        last_sale = max((i for i, o in enumerate(proposed) if o[:2] == ["SELL", "FERTILIZER"]), default=-1)
        index = next((i for i in range(len(proposed) - 1, last_sale, -1) if proposed[i][:2] == ["BUY_PRODUCT", "FERTILIZER"]), None)
        if index is not None:
            proposed[index][2] = max(0, int(proposed[index][2])) + shortage
        elif len(proposed) < 10:
            proposed.append(["BUY_PRODUCT", "FERTILIZER", shortage])
        else:
            _FG_REPORT["fg_declines"] += 1
            return action if not trimmed else result
        bought = shortage
    f, _, safe = project(proposed)
    if not safe or not _r97_budget(obs, proposed):
        _FG_REPORT["fg_declines"] += 1
        return action
    if not (trimmed or bought):
        return action
    _FG_REPORT["fg_changes"] += 1; _FG_REPORT["fg_trim"] += trimmed; _FG_REPORT["fg_buy"] += bought
    _FG_REPORT["fg_units"] += trimmed + bought
    return result


def agent(observation, configuration=None):
    action = _FG_PARENT(observation, configuration)
    try:
        if isinstance(action, dict):
            action = _fg_supply(observation, action)
    except Exception:
        _FG_REPORT["fg_errors"] += 1
    return action


agent.telemetry = _FG_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
