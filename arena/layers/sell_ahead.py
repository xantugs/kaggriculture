

# =====================================================================================
# Sell-ahead (days before the last): produce that is only ever sold (never fed, planted or
# spread) is sold as soon as it is in the shed, from the first order slots. Both farms share
# one market whose stock only drains slowly through town consumption, so a unit sold before
# the rival's lowers the rival's price, not ours. Orders the parent needs (hires, buys,
# wheat/fertilizer) are never displaced; the final day is left to the final-day controller.
# =====================================================================================
_SA_ITEMS = __ITEMS__
_SA_FROM = __FROM__
_SA_UNTIL = 696
_SA_PARENT = agent
def agent(observation, configuration=None):
    action = _SA_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step < _SA_FROM or step >= _SA_UNTIL or not isinstance(action, dict):
            return action
        shed = observation["private"]["shed"] or {}
        prices = observation["market"]["prices"] or {}
        market = [o for o in (action.get("market") or []) if isinstance(o, list)]
        parent_q = {}
        for o in market:
            if len(o) >= 3 and o[0] == "SELL" and o[1] in _SA_ITEMS:
                parent_q[o[1]] = parent_q.get(o[1], 0) + int(o[2])
        ours = []
        for item in _SA_ITEMS:
            q = max(int(shed.get(item, 0) or 0), parent_q.get(item, 0))
            if q > 0:
                ours.append((0 if item in parent_q else 1, -(q * int(prices.get(item, 1) or 1)), item, q))
        if not ours:
            return action
        items = {it for _, _, it, _ in ours}
        rest = [o for o in market if not (len(o) >= 2 and o[0] == "SELL" and o[1] in items)]
        room = max(0, 10 - len(rest))
        ours.sort()
        keep = ours[:room]
        keep.sort(key=lambda r: r[1])
        out = dict(action)
        out["market"] = [["SELL", it, q] for _, _, it, q in keep] + rest
        return out
    except Exception:
        return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
