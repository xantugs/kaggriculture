

# =====================================================================================
# Plot block: a demand-driven second crop on the opening melon plots.
# After the day-10 melon harvest the route replants these plots with short wheat cycles and
# visits them almost daily. On up to _PB_N of them the replanting becomes a tomato; the route's
# own daily visits keep it watered, and once it is ripe a visit harvests it instead (never
# leaving the plant two days without water). Tomatoes are sold by this layer.
# =====================================================================================
_PB_ON = __ON__
_PB_N = __N__
_PB_BUY_STEP = __BUY__
_PB_PLANT_TO = __TO__
_PB_GATE = __GATE__            # "always" or a callable name
_PB_FEED = __FEED__            # keep at least this much wheat in the shed while tomatoes displace wheat plots
_PB_STATE = {}
_PB_REPORT = dict(bought=0, planted=0, harvest_swaps=0, water_swaps=0, errors=0, gated_off=0)


def _pb_gate_ok(obs):
    if _PB_GATE == "always":
        return True
    try:
        return bool(globals()[_PB_GATE](obs))
    except Exception:
        return False


_PB_PARENT = agent
def agent(observation, configuration=None):
    action = _PB_PARENT(observation, configuration)
    if not _PB_ON:
        return action
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        st = _PB_STATE.get(seat)
        if st is None or step < st.get("last", -1):
            st = {"melon": set(), "owned": set(), "on": None, "last": -1}
            _PB_STATE[seat] = st
        st["last"] = step
        if not isinstance(action, dict) or step >= 696:
            return action
        farm = observation["farms"][seat]
        tiles = farm["tiles"]
        if step == 120:
            st["melon"] = {(x, y) for y, row in enumerate(tiles) for x, t in enumerate(row)
                           if isinstance(t, dict) and t.get("crop") == "MELON"}
        out = dict(action)
        market = list(action.get("market") or [])
        if step == _PB_BUY_STEP and st["melon"]:
            st["on"] = _pb_gate_ok(observation)
            if st["on"]:
                market = [["BUY_SEED", "TOMATO", _PB_N]] + market
                _PB_REPORT["bought"] += 1
            else:
                _PB_REPORT["gated_off"] += 1
        seeds = int((observation["private"].get("seeds") or {}).get("TOMATO", 0) or 0)
        positions = [tuple(farm["farmer"])] + [tuple(p) for p in (farm.get("hands") or [])]
        units = [action.get("farmer")] + list(action.get("hands") or [])
        new_units = list(units)
        for i, p in enumerate(positions):
            if i >= len(units):
                break
            u = units[i]
            if not isinstance(u, list) or not u:
                continue
            t = tiles[p[1]][p[0]]
            # convert the route's wheat replanting on a melon plot
            if (st["on"] and u[0] == "PLANT" and len(u) > 1 and u[1] == "WHEAT" and p in st["melon"]
                    and p not in st["owned"] and len(st["owned"]) < _PB_N and seeds > 0 and step < _PB_PLANT_TO and t is None):
                new_units[i] = ["PLANT", "TOMATO"]
                st["owned"].add(p)
                seeds -= 1
                _PB_REPORT["planted"] += 1
                continue
            if p in st["owned"] and isinstance(t, dict) and t.get("crop") == "TOMATO":
                ripe = int(t.get("yield_units", 0) or 0) > 0
                watered = bool(t.get("watered_today"))
                safe_skip = watered or int(t.get("consecutive_unwatered", 1) or 0) == 0
                if u[0] in ("WATER", "PLANT", "HARVEST", "FERTILIZE", "DIG"):
                    if ripe and (u[0] == "HARVEST" or safe_skip):
                        if u[0] != "HARVEST":
                            _PB_REPORT["harvest_swaps"] += 1
                        new_units[i] = ["HARVEST"]
                    elif u[0] in ("PLANT", "DIG", "HARVEST") and not watered:
                        new_units[i] = ["WATER"]
                        _PB_REPORT["water_swaps"] += 1
                    elif u[0] == "DIG":
                        new_units[i] = ["PASS"]
        out["farmer"] = new_units[0]
        out["hands"] = new_units[1:]
        shed = observation["private"].get("shed") or {}
        q = int(shed.get("TOMATO", 0) or 0)
        if q > 0 and not any(isinstance(o, list) and o and o[0] == "SELL" and len(o) > 1 and o[1] == "TOMATO" for o in market):
            market = [["SELL", "TOMATO", q]] + market
        if _PB_FEED and st["owned"] and 288 <= step < 624:
            w = int(shed.get("WHEAT", 0) or 0)
            if w < _PB_FEED:
                market = [["BUY_PRODUCT", "WHEAT", _PB_FEED - w]] + market
        out["market"] = market[:10]
        return out
    except Exception:
        _PB_REPORT["errors"] += 1
        return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
