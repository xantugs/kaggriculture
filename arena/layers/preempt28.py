

# ---- pre-empt the day-28 evening sale: premium goods still held are sold right after the town
# ---- purchase tick at step __STEP__ instead of waiting for the route's late sale, which a rival can learn and beat.
_PE_STEP = __STEP__
_PE_ITEMS = __ITEMS__
_PE_REPORT = dict(fired=0)
_PE_PARENT = agent
def agent(observation, configuration=None):
    action = _PE_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step != _PE_STEP or not isinstance(action, dict):
            return action
        shed = observation["private"].get("shed") or {}
        market = list(action.get("market") or [])
        have = {o[1] for o in market if isinstance(o, list) and len(o) > 1 and o[0] == "SELL"}
        pre = [["SELL", it, int(shed.get(it, 0))] for it in _PE_ITEMS if int(shed.get(it, 0) or 0) > 0 and it not in have]
        room = 10 - len(market)
        if pre and room > 0:
            _PE_REPORT["fired"] += 1
            out = dict(action); out["market"] = pre[:room] + market
            return out
    except Exception:
        pass
    return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
