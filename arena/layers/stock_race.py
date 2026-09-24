

# =====================================================================================
# Stock race. The route holds premium goods in the shed waiting for the town drain to lift
# the price. That pays when the rival is not sitting on the same good; when it is, whoever
# sells first takes the high prices. The rival's harvests are public (tile yield drops) and
# its sales show up as market-inventory changes net of our sales and town consumption, so
# its unsold stock can be estimated. While it holds a good we also hold, we sell ours first.
# =====================================================================================
_SR_ITEMS = __ITEMS__
_SR_MIN = __MIN__
_SR_STATE = {}
_SR_REPORT = dict(races=0, errors=0)
_SR_SHOP_ITEMS = {"BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
                  "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
                  "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
                  "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
                  "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY")}
_SR_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def _sr_draw(shops, step):
    draw = {}
    if step % 4 == 0:
        for s in shops:
            its = _SR_SHOP_ITEMS.get(s, ())
            for it in its:
                draw[it] = draw.get(it, 0) + (2 if len(its) == 1 else 1)
    if step % 24 == 0:
        for it in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"):
            draw[it] = draw.get(it, 0) + 1
    return draw


def _sr_units(t):
    if not isinstance(t, dict):
        return None, 0
    if t.get("kind") == "PLANT":
        return t.get("crop"), int(t.get("yield_units", 0) or 0)
    if t.get("animal"):
        return _SR_PRODUCT.get(t["animal"]), int(t.get("yield_units", 0) or 0)
    return None, 0


_SR_PARENT = agent
def agent(observation, configuration=None):
    action = _SR_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        st = _SR_STATE.get(seat)
        if st is None or step <= st.get("step", -1):
            st = {"step": -1, "stock": {}, "prev": None}
            _SR_STATE[seat] = st
        rival = observation["farms"][1 - seat]
        inv = observation["market"]["inventory"]
        prev = st["prev"]
        if prev is not None and prev["step"] == step - 1:
            # rival harvests since last turn
            for y, row in enumerate(rival["tiles"]):
                for x, t in enumerate(row):
                    i0, u0 = _sr_units(prev["tiles"][y][x])
                    i1, u1 = _sr_units(t)
                    if i0 in _SR_ITEMS and u0 > 0:
                        took = u0 - (u1 if i1 == i0 else 0)
                        # decay of ripe plants is not a harvest; only count drops of 1+ units at a unit's position
                        if took > 0 and (x, y) in prev["rival_pos"]:
                            st["stock"][i0] = st["stock"].get(i0, 0) + took
            # rival sales last turn: inventory rise not explained by our sales, net of town consumption
            draw = _sr_draw(prev["shops"], prev["step"])
            for it in _SR_ITEMS:
                sold = inv[it] - prev["inv"][it] + draw.get(it, 0) - prev["own"].get(it, 0)
                if sold > 0:
                    st["stock"][it] = max(0, st["stock"].get(it, 0) - sold)
        # end of day: stock carries over (rival inventories drop into its shed)
        out = action
        if isinstance(action, dict) and step < 696:
            shed = observation["private"].get("shed") or {}
            market = list(action.get("market") or [])
            have = {o[1] for o in market if isinstance(o, list) and len(o) > 1 and o[0] == "SELL"}
            pre = []
            for it in _SR_ITEMS:
                q = int(shed.get(it, 0) or 0)
                if q > 0 and it not in have and st["stock"].get(it, 0) >= _SR_MIN:
                    pre.append(["SELL", it, q])
            room = 10 - len(market)
            if pre and room > 0:
                out = dict(action); out["market"] = pre[:room] + market
                _SR_REPORT["races"] += 1
        # our own sells this turn (for next turn's inference): what we can actually deliver
        own = {}
        if isinstance(out, dict):
            shed = observation["private"].get("shed") or {}
            for o in (out.get("market") or []):
                if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] in _SR_ITEMS:
                    own[o[1]] = min(int(shed.get(o[1], 0) or 0), own.get(o[1], 0) + int(o[2]))
        st["prev"] = {"step": step, "inv": dict(inv), "own": own, "shops": list(observation["town"]["unlocked_shops"] or []),
                      "tiles": [list(r) for r in rival["tiles"]],
                      "rival_pos": {tuple(rival["farmer"])} | {tuple(p) for p in (rival.get("hands") or [])}}
        st["step"] = step
        return out
    except Exception:
        _SR_REPORT["errors"] += 1
        return action
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
