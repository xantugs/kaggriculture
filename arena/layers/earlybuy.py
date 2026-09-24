# ---------------------------------------------------------------------------
# Local modification (Apache-2.0 notice) by offhand, 2026-09-22.
# EARLYBUY: buy the tape's fertilizer one turn early.
# The route tapes buy small fertilizer lots at fixed turns.  A copy of the tape can
# buy a large lot in slot 0 of that turn and sell it back at the end of the same turn,
# so our lot fills at the top of its pump (Roman Katasonov: ~$1.2k/game).  Buying the
# lot in slot 0 of the previous turn leaves the pump nothing to sell into.
# ---------------------------------------------------------------------------
_EB_CFG = _EB_CFG_PLACEHOLDER
_EB_PARENT = agent
_EB_REPORT = {"eb_prebuys": 0, "eb_units": 0, "eb_trimmed": 0, "eb_errors": 0}
_EB_STATE = {"pending": {}}


def _eb_tape_buy(step, route, item):
    try:
        a = _IMPL.chassis.routes[2 if step >= 648 else route][step]
    except Exception:
        return 0
    if not isinstance(a, dict):
        return 0
    return sum(max(0, int(o[2])) for o in (a.get("market") or [])
               if isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == item)


def agent(observation, configuration=None):
    action = _EB_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step == 0:
            _EB_STATE["pending"] = {}
            for k in _EB_REPORT:
                _EB_REPORT[k] = 0
        if not isinstance(action, dict):
            return action
        market = [list(o) for o in (action.get("market") or [])]
        changed = False
        # 1) this turn's tape buy was made last turn: take it out of the parent's queue
        owed = _EB_STATE["pending"].pop(step, {})
        if owed:
            kept = []
            for o in market:
                item = o[1] if len(o) >= 2 else None
                if item in owed and owed[item] > 0 and len(o) >= 3 and o[0] == "BUY_PRODUCT":
                    q = max(0, int(o[2]))
                    take = min(q, owed[item])
                    owed[item] -= take
                    if q - take > 0:
                        kept.append(["BUY_PRODUCT", item, q - take])
                    _EB_REPORT["eb_trimmed"] += take
                    continue
                kept.append(o)
            market, changed = kept, True
        # 2) pre-buy next turn's tape lot in slot 0 now
        if _EB_CFG.get("from", 144) <= step < _EB_CFG.get("to", 690):
            native = _IMPL.chassis.players.get(int(observation["player"]))
            if native:
                prices = observation["market"]["prices"]
                money = float(observation["farms"][int(observation["player"])]["money"])
                pre = []
                for item in _EB_CFG.get("items", ("FERTILIZER",)):
                    q = _eb_tape_buy(step + 1, native.get("route"), item)
                    if q <= 0 or any(len(o) >= 2 and o[0] == "SELL" and o[1] == item for o in market):
                        continue
                    cost = q * (int(prices.get(item, 50)) + 5)
                    if money < 2 * cost + 1000:
                        continue
                    pre.append(["BUY_PRODUCT", item, q])
                    _EB_STATE["pending"].setdefault(step + 1, {})[item] = q
                    _EB_REPORT["eb_prebuys"] += 1
                    _EB_REPORT["eb_units"] += q
                    money -= cost
                if pre and len(pre) + len(market) <= 10:
                    market, changed = pre + market, True
                elif pre:
                    for p in pre:
                        _EB_STATE["pending"].get(step + 1, {}).pop(p[1], None)
        return dict(action, market=market) if changed else action
    except Exception:
        _EB_REPORT["eb_errors"] += 1
        return action


agent.telemetry = _EB_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
