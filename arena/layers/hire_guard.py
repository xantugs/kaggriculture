

# =====================================================================================
# Hire guard. The scripted opening runs its cash down to a few dollars, so a rival that
# moves the wheat price on the first turns can leave us short at a scripted hire, and a
# failed day-1 hire breaks the whole route. When this turn's HIRE orders cost more than we
# can pay, sell just enough stock first (fertilizer, then eggs, then wheat) to cover them.
# =====================================================================================
_HG_ORDER = ("FERTILIZER", "EGG", "WHEAT", "CARROT", "MILK", "WOOL", "TOMATO", "STRAWBERRY", "MELON")
_HG_REPORT = dict(guards=0, errors=0)


def _hg_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


_HG_PARENT = agent
def agent(observation, configuration=None):
    action = _HG_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step >= 696 or not isinstance(action, dict):
            return action
        market = [o for o in (action.get("market") or []) if isinstance(o, list)]
        n_hire = sum(1 for o in market if o and o[0] == "HIRE")
        if not n_hire:
            return action
        seat = int(observation["player"])
        farm = observation["farms"][seat]
        money = float(farm.get("money", 0))
        done = int(farm.get("hires_today", 0) or 0)
        need = sum(_hg_fib(done + i) for i in range(n_hire))
        prices = observation["market"]["prices"] or {}
        # purchases queued ahead of the hires also draw on the same cash
        for o in market:
            if o[0] == "HIRE":
                break
            if o[0] in ("BUY_PRODUCT",) and len(o) >= 3:
                need += int(o[2]) * int(prices.get(o[1], 0) or 0)
            elif o[0] == "BUY_SEED" and len(o) >= 3:
                need += int(o[2]) * {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}.get(o[1], 0)
            elif o[0] == "BUY_ANIMAL" and len(o) >= 3:
                need += int(o[2]) * {"GOOSE": 300, "COW": 400, "SHEEP": 500}.get(o[1], 0)
        short = need - money
        if short <= 0:
            return action
        shed = observation["private"]["shed"] or {}
        sells = []
        for item in _HG_ORDER:
            q, p = int(shed.get(item, 0) or 0), int(prices.get(item, 0) or 0)
            if q <= 0 or p <= 1:
                continue
            k = min(q, int(short // p) + 1)
            sells.append(["SELL", item, k])
            short -= k * p
            if short <= 0:
                break
        if not sells:
            return action
        _HG_REPORT["guards"] += 1
        out = dict(action)
        out["market"] = (sells + market)[:10]
        return out
    except Exception:
        _HG_REPORT["errors"] += 1
        return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
