

# ---- experiment: sell listed goods as soon as they are in the shed (before the final day) ----
_WN_ITEMS = __ITEMS__
_WN_PARENT = agent
def agent(observation, configuration=None):
    action = _WN_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step >= 696 or not isinstance(action, dict):
            return action
        shed = observation["private"].get("shed") or {}
        market = list(action.get("market") or [])
        have = {o[1] for o in market if isinstance(o, list) and len(o) > 1 and o[0] == "SELL"}
        pre = []
        for item in _WN_ITEMS:
            q = int(shed.get(item, 0) or 0)
            if q > 0 and item not in have:
                pre.append(["SELL", item, q])
        room = 10 - len(market)
        if pre and room > 0:
            out = dict(action); out["market"] = pre[:room] + market
            return out
    except Exception:
        pass
    return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
