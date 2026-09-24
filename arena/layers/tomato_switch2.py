

# =====================================================================================
# Tomato switch. The route plants strawberries by a fixed script; when tomatoes pay more,
# strawberry seed purchases and plantings are switched to tomatoes (ready on days 8-11 after
# planting instead of 10-16, half the seed cost). The route keeps seeing its strawberry seed
# count, so its plan is undisturbed; switched tomatoes are sold by this layer.
# =====================================================================================
_TS_MODE = __MODE__          # "all" or "ratio"
_TS_RATIO = __RATIO__        # switch when tomato price >= ratio * strawberry price
_TS_FROM = __FROM__
_TS_UNTIL = __UNTIL__
_TS_STATE = {}
_TS_REPORT = dict(switched_buys=0, switched_plants=0, errors=0)


def _ts_want(obs):
    if _TS_MODE == "all":
        return True
    pr = obs["market"]["prices"]
    return float(pr.get("TOMATO", 0)) >= _TS_RATIO * float(pr.get("STRAWBERRY", 1))


def _ts_view(obs, conv):
    if conv <= 0:
        return obs
    o = dict(obs)
    p = dict(obs["private"])
    s = dict(p.get("seeds") or {})
    s["STRAWBERRY"] = int(s.get("STRAWBERRY", 0)) + conv
    s["TOMATO"] = max(0, int(s.get("TOMATO", 0)) - conv)
    p["seeds"] = s
    o["private"] = p
    return o


_TS_PARENT = agent
def agent(observation, configuration=None):
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        st = _TS_STATE.get(seat)
        if st is None or step < st.get("last", -1):
            st = {"conv": 0, "last": -1, "pend": None}
            _TS_STATE[seat] = st
        seeds = observation["private"].get("seeds") or {}
        tom = int(seeds.get("TOMATO", 0) or 0)
        # reconcile: converted seeds can never exceed the tomato seeds actually held
        if st["pend"] is not None:
            got = max(0, tom - st["pend"]["tom_before"] + st["pend"]["planted"])
            st["conv"] = max(0, min(tom, st["conv"] - st["pend"]["planted"] + min(got, st["pend"]["bought"])))
        st["conv"] = min(st["conv"], tom)
        st["last"] = step
        action = _TS_PARENT(_ts_view(observation, st["conv"]), configuration)
        if not isinstance(action, dict) or step >= 696:
            st["pend"] = None
            return action
        out = dict(action)
        bought = 0
        market = []
        for o in (action.get("market") or []):
            if (isinstance(o, list) and len(o) >= 3 and o[0] == "BUY_SEED" and o[1] == "STRAWBERRY"
                    and _TS_FROM <= step < _TS_UNTIL and _ts_want(observation)):
                market.append(["BUY_SEED", "TOMATO", o[2]])
                bought += int(o[2])
                _TS_REPORT["switched_buys"] += 1
            else:
                market.append(o)
        # plantings: use converted tomato seeds first
        planted = 0
        avail = st["conv"]
        def conv(u):
            nonlocal planted, avail
            if isinstance(u, list) and len(u) >= 2 and u[0] == "PLANT" and u[1] == "STRAWBERRY" and avail > 0:
                avail -= 1
                planted += 1
                _TS_REPORT["switched_plants"] += 1
                return ["PLANT", "TOMATO"]
            return u
        out["farmer"] = conv(action.get("farmer"))
        out["hands"] = [conv(u) for u in (action.get("hands") or [])]
        # sell switched tomatoes from the shed (the route has no plan for them)
        shed = observation["private"].get("shed") or {}
        q = int(shed.get("TOMATO", 0) or 0)
        if q > 0 and len(market) < 10 and not any(isinstance(o, list) and o and o[0] == "SELL" and len(o) > 1 and o[1] == "TOMATO" for o in market):
            market = [["SELL", "TOMATO", q]] + market
        out["market"] = market
        st["pend"] = {"tom_before": tom, "planted": planted, "bought": bought}
        return out
    except Exception:
        _TS_REPORT["errors"] += 1
        return _TS_PARENT(observation, configuration)
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
