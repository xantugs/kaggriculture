

# =====================================================================================
# Opening squeeze. Both farms trade wheat on the first turn and settle unit by unit in
# lockstep, so the size of our round trip moves the prices the rival gets. The route-0
# chassis spends its opening cash down to a few dollars; a smaller first-turn round trip
# (the same net wheat, bought one turn later) leaves a mirror rival ~$11 short, which is
# enough to fail its day-1 hires. Our own route is unchanged.
# =====================================================================================
_SQ_STEP0 = __STEP0__
_SQ_STEP1_PRE = __STEP1__
_SQ_PARENT = agent
def agent(observation, configuration=None):
    action = _SQ_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step == 0 and isinstance(action, dict):
            out = dict(action); out["market"] = [list(o) for o in _SQ_STEP0]
            return out
        if step == 1 and isinstance(action, dict):
            out = dict(action)
            out["market"] = ([list(o) for o in _SQ_STEP1_PRE] + list(action.get("market") or []))[:10]
            return out
    except Exception:
        pass
    return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
