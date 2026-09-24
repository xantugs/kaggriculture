# ---------------------------------------------------------------------------
# DRIP: sell premium lots as the book allows instead of in the tape's big lots.
# Wool (and milk) books saturate in herd towns; the town drain then re-opens the
# book a unit or two at a time.  A rival that sells each unit as soon as the price
# has recovered takes all of that recovery, and the tape's 12-unit dumps land in a
# $1 book.  Each turn from DRIP_FROM to DRIP_TO this layer replaces our sales of the
# listed items with: every unit in the shed whose marginal quote is >= its floor
# (sold first in the market queue), plus whatever exceeds DRIP_CAP in the shed.
# ---------------------------------------------------------------------------
_DRIP_CFG = _DRIP_CFG_PLACEHOLDER
_DRIP_PARENT = agent
_DRIP_SHOP_ITEMS = {"BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"), "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",), "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",), "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"), "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")}
_DRIP_REPORT = {"drip_turns": 0, "drip_units": 0, "drip_held": 0, "drip_errors": 0}


def _drip_act(obs, action):
    step = int(obs["step"])
    if not _DRIP_CFG.get("from", 192) <= step < _DRIP_CFG.get("to", 696):
        return action
    floors = _DRIP_CFG.get("floors", {})
    market = [list(o) for o in (action.get("market") or [])]
    # never touch a turn whose queue we cannot rebuild safely
    if any(len(o) >= 2 and o[0] == "BUY_PRODUCT" and o[1] in floors for o in market):
        return action
    view = FarmView(obs)
    stock = projected_shed(action, view)
    inv = obs["market"]["inventory"]
    cap = int(_DRIP_CFG.get("cap", 10))
    held_total = sum(max(0, int(stock.get(i, 0))) for i in floors)
    sells = []
    for item in _DRIP_CFG.get("order", list(floors)):
        if item not in floors:
            continue
        have = max(0, int(stock.get(item, 0)))
        if have <= 0:
            continue
        floor = floors[item]
        q, level = 0, int(inv[item])
        while q < have and _r37_market_price(item, level) >= floor:
            q += 1
            level += 1
        # hold only where the town drains the book again (units/turn), and only a few units
        shops = list(obs["town"].get("unlocked_shops") or [])
        drain = sum((0.5 if len(_DRIP_SHOP_ITEMS.get(s_, ())) == 1 else 0.25) for s_ in shops if item in _DRIP_SHOP_ITEMS.get(s_, ())) + 1 / 24
        room = 100 - sum(max(0, int(v)) for v in stock.values())
        keep = cap if drain >= _DRIP_CFG.get("min_drain", 0.4) else 0
        keep = min(keep, max(0, room - int(_DRIP_CFG.get("room", 40))))
        if have - q > keep:
            q = have - keep
        held_total -= q
        if q > 0:
            sells.append(["SELL", item, q])
            _DRIP_REPORT["drip_units"] += q
        _DRIP_REPORT["drip_held"] += have - q
    rest = [o for o in market if not (len(o) >= 2 and o[0] == "SELL" and o[1] in floors)]
    new = sells + rest
    if len(new) > 10:
        # keep our sells; drop the tail of the parent's queue only if it holds no buys/hires
        tail = new[10:]
        if any(o and o[0] != "SELL" for o in tail):
            return action
        new = new[:10]
    _DRIP_REPORT["drip_turns"] += 1
    return dict(action, market=new)


def agent(observation, configuration=None):
    action = _DRIP_PARENT(observation, configuration)
    try:
        if int(observation["step"]) == 0:
            for k in _DRIP_REPORT:
                _DRIP_REPORT[k] = 0
        if isinstance(action, dict):
            return _drip_act(observation, action)
    except Exception:
        _DRIP_REPORT["drip_errors"] += 1
    return action


agent.telemetry = _DRIP_REPORT
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
