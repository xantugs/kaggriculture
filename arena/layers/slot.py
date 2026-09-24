# ---------------------------------------------------------------------------
# Local modification (Apache-2.0 notice) by offhand, 2026-09-22.
# SLOT: order our same-turn sales to win the lockstep races a mirror would tie.
# Both farms' i-th orders settle unit by unit together, so a product we list
# before the rival lists it is sold entirely before the rival's lot, and one we
# list after it lands in the rival's crash.  A mirror lists its sales in the
# parent's order.  Against that order, pick the permutation of our premium sales
# that maximizes  sum(win adv) - sum(lose adv),  adv(X) = our revenue selling X
# ahead of an equal rival lot minus behind it.
# ---------------------------------------------------------------------------
import itertools as _slot_it
_SLOT_CFG = _SLOT_CFG_PLACEHOLDER
_SLOT_PARENT = agent
_SLOT_REPORT = {"slot_turns": 0, "slot_gain": 0, "slot_errors": 0}


def _slot_adv(item, inv, q):
    before = sum(_r37_market_price(item, inv + k) for k in range(q))
    after = sum(_r37_market_price(item, inv + q + k) for k in range(q))
    return before - after


def _slot_act(obs, action):
    step = int(obs["step"])
    if not _SLOT_CFG.get("from", 192) <= step < _SLOT_CFG.get("to", 696):
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if any(len(o) >= 2 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" for o in market) and any(len(o) >= 2 and o[0] == "SELL" and o[1] == "WHEAT" for o in market):
        return action  # a same-step wheat trip: keep its slots
    lead = 0
    while lead < len(market) and len(market[lead]) >= 3 and market[lead][0] == "SELL":
        lead += 1
    sells, rest = market[:lead], market[lead:]
    items = [o[1] for o in sells]
    if len(sells) < 2 or len(sells) > 5 or len(set(items)) != len(items):
        return action
    inv = obs["market"]["inventory"]
    view = FarmView(obs)
    stock = projected_shed(action, view)
    adv = {}
    for o in sells:
        q = min(max(0, int(o[2])), max(0, int(stock.get(o[1], 0))), 60)
        adv[o[1]] = _slot_adv(o[1], int(inv[o[1]]), q) if q > 0 else 0
    rival_pos = {it: i for i, it in enumerate(items)}   # a mirror's queue: the parent's order
    best, best_gain = sells, 0
    for perm in _slot_it.permutations(range(len(sells))):
        order = [sells[i] for i in perm]
        gain = 0
        for pos, o in enumerate(order):
            rp = rival_pos[o[1]]
            if pos < rp:
                gain += adv[o[1]]
            elif pos > rp:
                gain -= adv[o[1]]
        if gain > best_gain + _SLOT_CFG.get("min_gain", 5):
            best, best_gain = order, gain
    if best is sells:
        return action
    _SLOT_REPORT["slot_turns"] += 1
    _SLOT_REPORT["slot_gain"] += int(best_gain)
    return dict(action, market=best + rest)


def _slot_buyfirst(obs, action):
    """Grain/fertilizer buys ahead of fixed-price orders (seeds, animals, hires, land) and of our small
    fertilizer sales: a mirror that lists its buy earlier buys before us; nothing else depends on the order."""
    step = int(obs["step"])
    if step < 144 or step >= 696:
        return action
    market = [list(o) for o in (action.get("market") or [])]
    if any(len(o) >= 2 and o[0] == "SELL" and o[1] == "WHEAT" for o in market):
        return action
    buys = [o for o in market if len(o) >= 3 and o[0] == "BUY_PRODUCT"]
    if not buys:
        return action
    premium = [o for o in market if len(o) >= 2 and o[0] == "SELL" and o[1] != "FERTILIZER"]
    low = [o for o in market if len(o) >= 2 and o[0] == "SELL" and o[1] == "FERTILIZER"]
    others = [o for o in market if not (len(o) >= 2 and o[0] == "SELL") and not (len(o) >= 3 and o[0] == "BUY_PRODUCT")]
    if any(len(b) >= 2 and b[1] == "FERTILIZER" for b in buys) and low:
        return action  # keep a fertilizer sell/buy pair in its own order
    new = premium + buys + low + others
    if new == market:
        return action
    prices = obs["market"]["prices"]
    cost = sum(max(0, int(o[2])) * (int(prices.get(o[1], 50)) + 5) for o in buys)
    if float(obs["farms"][int(obs["player"])]["money"]) < 2 * cost + 1000:
        return action
    _SLOT_REPORT["buyfirst_turns"] = _SLOT_REPORT.get("buyfirst_turns", 0) + 1
    return dict(action, market=new)


def agent(observation, configuration=None):
    action = _SLOT_PARENT(observation, configuration)
    try:
        if int(observation["step"]) == 0:
            for k in _SLOT_REPORT:
                _SLOT_REPORT[k] = 0
        if isinstance(action, dict) and len(action.get("market") or []) <= 8:
            action = _slot_act(observation, action)
        if isinstance(action, dict) and _SLOT_CFG.get("buyfirst"):
            action = _slot_buyfirst(observation, action)
    except Exception:
        _SLOT_REPORT["slot_errors"] += 1
    return action


agent.telemetry = _SLOT_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
