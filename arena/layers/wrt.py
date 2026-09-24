# ---------------------------------------------------------------------------
# Local modification (Apache-2.0 notice) by offhand, 2026-09-22.
# WRT: same-step wheat round trips.
# Some route tapes (103/104/112/124) buy wheat right before a town draw and sell the
# same quantity one or two steps later.  A copy of the tape that does BUY q / SELL q inside
# one step (BUY first) sells at the peak of our own buying and takes ~q^2/2 *
# slope from us per trip (-$5.4k in the A. R. SEKKAT loss).  Doing the trip in
# one step (BUY at slot 0, SELL at slot 1) ties with such copies and takes the
# same edge from plain copies of the tape.
# ---------------------------------------------------------------------------
_WRT_CFG = _WRT_CFG_PLACEHOLDER
_WRT_PARENT = agent
_WRT_REPORT = {"wrt_converted": 0, "wrt_units": 0, "wrt_next_trimmed": 0, "wrt_rebuy_units": 0, "wrt_rebuy_blocked": 0, "wrt_errors": 0}
_WRT_STATE = {"pending": None}


def _wrt_tape(step, route):
    try:
        return _IMPL.chassis.routes[2 if step >= 648 else route][step]
    except Exception:
        return None


def _wrt_split_qty(step, route):
    """(q, k): the tape buys q wheat at `step` (no wheat sale there) and sells exactly q at step+k (k<=K),
    with no wheat buy/sale/pickup in between and no pickup at the sale step."""
    a = _wrt_tape(step, route)
    if not isinstance(a, dict):
        return 0, 0
    ma = [o for o in (a.get("market") or []) if isinstance(o, list) and len(o) >= 3]
    buys = [int(o[2]) for o in ma if o[0] == "BUY_PRODUCT" and o[1] == "WHEAT"]
    if len(buys) != 1 or any(o[0] == "SELL" and o[1] == "WHEAT" for o in ma):
        return 0, 0
    q = buys[0]
    if q <= 0:
        return 0, 0
    for k in range(1, int(_WRT_CFG.get("kmax", 1)) + 1):
        b = _wrt_tape(step + k, route)
        if not isinstance(b, dict):
            return 0, 0
        cmds = [b.get("farmer") or ["PASS"], *(b.get("hands") or [])]
        if any(isinstance(c, list) and c[:2] == ["PICKUP", "WHEAT"] for c in cmds):
            return 0, 0
        mb = [o for o in (b.get("market") or []) if isinstance(o, list) and len(o) >= 3]
        sells = [int(o[2]) for o in mb if o[0] == "SELL" and o[1] == "WHEAT"]
        if any(o[0] == "BUY_PRODUCT" and o[1] == "WHEAT" for o in mb):
            return 0, 0
        if sells:
            return (q, k) if sells == [q] else (0, 0)
    return 0, 0


def agent(observation, configuration=None):
    action = _WRT_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        if step == 0:
            _WRT_STATE["pending"] = None
            for k in _WRT_REPORT:
                _WRT_REPORT[k] = 0
        if not isinstance(action, dict):
            return action
        pend = _WRT_STATE["pending"]
        if pend is not None:
            # the tape's sale of this lot was already made in the buy step: strip the parent's wheat
            # sales (the tape sale, or a reservation pulling it forward) up to the lot size
            last, owed = pend
            if step > last:
                _WRT_STATE["pending"] = pend = None
            else:
                market = [list(o) for o in (action.get("market") or [])]
                kept = []
                for o in market:
                    if owed > 0 and len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT":
                        q = max(0, int(o[2]))
                        take = min(q, owed)
                        owed -= take
                        if q - take > 0:
                            kept.append(["SELL", "WHEAT", q - take])
                        continue
                    kept.append(o)
                if owed > 0 and step == last and _WRT_CFG.get("rebuy", False):
                    if len(kept) < 10:
                        kept.append(["BUY_PRODUCT", "WHEAT", owed])
                        _WRT_REPORT["wrt_rebuy_units"] += owed
                    else:
                        _WRT_REPORT["wrt_rebuy_blocked"] += 1
                _WRT_STATE["pending"] = None if (step == last or owed <= 0) else (last, owed)
                if step == last or owed <= 0:
                    _WRT_REPORT["wrt_next_trimmed"] += 1
                action = dict(action, market=kept)
        if step < 2 or step >= 646 or _WRT_STATE["pending"] is not None:
            return action
        native = _IMPL.chassis.players.get(int(observation["player"]))
        if not native:
            return action
        q, k = _wrt_split_qty(step, native.get("route"))
        if q <= 0 or step + k >= 696:
            return action
        market = [list(o) for o in (action.get("market") or [])]
        bi = [i for i, o in enumerate(market) if len(o) >= 3 and o[0] == "BUY_PRODUCT" and o[1] == "WHEAT"]
        if len(bi) != 1 or any(len(o) >= 3 and o[0] == "SELL" and o[1] == "WHEAT" for o in market):
            return action
        qa = int(market[bi[0]][2])
        if qa <= 0:
            return action
        mode = _WRT_CFG.get("mode", "same")
        rest = [o for i, o in enumerate(market) if i != bi[0]]
        if mode == "same":
            new = [["BUY_PRODUCT", "WHEAT", qa], ["SELL", "WHEAT", qa]] + rest
        elif mode == "skip":
            new = rest
        else:
            return action
        if len(new) > 10:
            return action
        _WRT_STATE["pending"] = (step + k, qa)
        _WRT_REPORT["wrt_converted"] += 1
        _WRT_REPORT["wrt_units"] += qa
        return dict(action, market=new)
    except Exception:
        _WRT_REPORT["wrt_errors"] += 1
        return action


agent.telemetry = _WRT_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
