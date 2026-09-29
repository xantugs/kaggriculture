
# >>> CDP: the forecast DP seller also times the tape's premium lots during the chassis (tape) phase.
# GC_P["cdp"] = {"from_day": 12, "prods": [...], "margin": 10}. Each chassis-phase step from from_day, our SELL orders for the
# premium products are replaced by the programme's decision on the shed stock after this turn's drops (units held stay in the
# shed; the chassis re-offers them next turn and the programme decides again). Steps whose list buys or hires keep the tape's
# own sells (its cash plan needs them). Held units never exceed tonight's shed room.
def _cdp_apply(observation, action, shed_):
    cfg = GC_P.get("cdp")
    if not cfg or not isinstance(action, dict):
        return action
    step = int(observation["step"]); day, hour = divmod(step, 24)
    if day < int(cfg.get("from_day", 12)) or day >= 29 or step >= 716:
        return action
    market = [o for o in (action.get("market") or []) if isinstance(o, list) and o]
    prods = tuple(cfg.get("prods", ("STRAWBERRY", "MILK", "WOOL")))
    if any(o[0] in ("HIRE", "BUY_LAND", "BUY_ANIMAL", "BUY_SEED", "BUY_PRODUCT") for o in market):
        _GC_REPORT["cdp_skip_buy"] = _GC_REPORT.get("cdp_skip_buy", 0) + 1
        return action
    try:
        _GC.me = int(observation["player"])
        carried = {}
        for inv_ in list(observation["private"].get("inventories") or []):
            for k_, v_ in dict(inv_).items():
                carried[k_] = carried.get(k_, 0) + int(v_)
        _GC.carried_items = carried
        shops = list(_gc_get(observation["town"], "unlocked_shops", []) or [])
        others = [o for o in market if not (o[0] == "SELL" and len(o) >= 2 and o[1] in prods)]
        other_sold = sum(int(o[2]) for o in others if o[0] == "SELL" and len(o) >= 3)
        room0 = 100 - (sum(int(v) for v in shed_.values()) - other_sold) - sum(carried.values()) - int(cfg.get("margin", 10))
        room = room0
        dec = {}
        for p in prods:
            n = int(shed_.get(p, 0))
            if n <= 0:
                continue
            x = _GC._dp_sell(observation, p, n, step, day, hour, shops, cap_night=max(0, room))
            x = 0 if x is None else max(0, min(n, int(x)))
            dec[p] = [n, x]
            room -= (n - x)
        if hour >= 20 and room < 0:
            # tonight's drop must fit: release held units, largest holding first
            need = -room
            for p in sorted(dec, key=lambda q: -(dec[q][0] - dec[q][1])):
                if need <= 0:
                    break
                add = min(need, dec[p][0] - dec[p][1])
                dec[p][1] += add; need -= add
            _GC_REPORT["cdp_released"] = _GC_REPORT.get("cdp_released", 0) + 1
        new_sells = []
        for p, (n, x) in dec.items():
            if x > 0:
                new_sells.append(["SELL", p, x])
            _GC_REPORT["cdp_held"] = _GC_REPORT.get("cdp_held", 0) + (n - x)
            _GC_REPORT["cdp_sold"] = _GC_REPORT.get("cdp_sold", 0) + x
        action = dict(action)
        action["market"] = new_sells + others
    except Exception as e:
        _GC_REPORT["cdp_err"] = repr(e)[:160]
    return action
# <<< CDP

cdp_submission_agent = agent
