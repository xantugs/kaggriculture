

# ---- experiment: late carrot plantings become wheat when wheat pays at least as much ----
_LW_FROM = __FROM__
_LW_RATIO = __RATIO__
_LW_PARENT = agent
def agent(observation, configuration=None):
    action = _LW_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step < _LW_FROM or step >= 696 or not isinstance(action, dict):
            return action
        pr = observation["market"]["prices"]
        if float(pr.get("WHEAT", 0)) < _LW_RATIO * float(pr.get("CARROT", 0)):
            return action
        out = dict(action)
        conv = lambda u: ["PLANT", "WHEAT"] if isinstance(u, list) and len(u) >= 2 and u[0] == "PLANT" and u[1] == "CARROT" else u
        out["farmer"] = conv(action.get("farmer"))
        out["hands"] = [conv(u) for u in (action.get("hands") or [])]
        out["market"] = [["BUY_SEED", "WHEAT", o[2]] if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" and o[1] == "CARROT" else o
                         for o in (action.get("market") or [])]
        return out
    except Exception:
        return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
