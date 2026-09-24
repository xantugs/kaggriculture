

# =====================================================================================
# Final-day controller v2 (day 29, steps 696..718): lean harvest tours + front-running.
# * Harvest: greedy value-per-step tours, only as many hires as pay for themselves; units
#   re-read the board every step (closed loop), deliver as soon as their tour is done.
# * Selling: staples are sold on delivery. Price-sensitive goods (milk, wool, strawberry,
#   melon, tomato) are held in the shed and sold one step before the rival can dump the same
#   good: the rival's tile yields are public, so a rival unit that harvested such a good is
#   tracked until it reaches the shed. Anything still held is sold from step _FD_FLUSH on.
# =====================================================================================
_FD_START = 696
_FD_LAST = 718
_FD_FLUSH = 716
_FD_CROPS = {
    "WHEAT": (2, 4, False, 6), "CARROT": (2, 3, False, 4), "TOMATO": (8, 8, True, 4),
    "STRAWBERRY": (10, 10, True, 4), "MELON": (10, 12, False, 6),
}
_FD_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
_FD_ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
_FD_HOLD = ("MILK", "WOOL", "STRAWBERRY", "MELON", "TOMATO")
_FD_STATE = {}
_FD_REPORT = dict(plans=0, hires=0, errors=0, fronts=0)


def _fd_fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def _fd_shed_tiles(board):
    h = board // 2
    return [(h - 1, h - 1), (h, h - 1), (h - 1, h), (h, h)]


def _fd_dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _fd_step_toward(a, b):
    if a[0] != b[0]:
        return "EAST" if b[0] > a[0] else "WEST"
    if a[1] != b[1]:
        return "SOUTH" if b[1] > a[1] else "NORTH"
    return None


def _fd_tile_info(t, day):
    if not isinstance(t, dict):
        return None
    if t.get("kind") == "PLANT":
        spec = _FD_CROPS.get(t.get("crop"))
        if spec is None:
            return None
        fyd, myd, ongoing, maxy = spec
        units = int(t.get("yield_units", 0) or 0)
        age = day - int(t.get("planted_day", day))
        if not ongoing and age < fyd:
            return None
        bonus = 0
        if not ongoing and not t.get("watered_today"):
            if (myd + 1) // 2 <= age <= myd:
                b = 2 if int(t.get("fertilized_until_day", -1)) >= day else 1
                bonus = max(0, min(maxy, units + b) - units)
        if units + bonus <= 0:
            return None
        return (t["crop"], units, bonus, int(t.get("max_lifespan_step", -1)))
    if t.get("animal"):
        units = int(t.get("yield_units", 0) or 0)
        if units > 0:
            return (_FD_PRODUCT.get(t["animal"], "MILK"), units, 0, -1)
    return None


def _fd_tile_units(t):
    """(product, units) on a tile regardless of harvestability (for rival tracking)."""
    if not isinstance(t, dict):
        return None, 0
    if t.get("kind") == "PLANT":
        return t.get("crop"), int(t.get("yield_units", 0) or 0)
    if t.get("animal"):
        return _FD_PRODUCT.get(t["animal"]), int(t.get("yield_units", 0) or 0)
    return None, 0


def _fd_units_at(units, mls, now, step):
    if mls >= 0 and step > mls:
        lo = max(now, mls)
        n = 0
        for s in range(lo, step):
            if (s - mls) % 2 == 0:
                n += 1
        units -= n
    return max(0, units)


def _fd_plan(obs):
    seat = int(obs["player"])
    farm = obs["farms"][seat]
    tiles = farm["tiles"]
    board = len(tiles)
    day = int(obs["day"])
    now = int(obs["step"])
    prices = {k: int(v) for k, v in (obs["market"]["prices"] or {}).items()}
    targets = []
    for y, row in enumerate(tiles):
        for x, t in enumerate(row):
            info = _fd_tile_info(t, day)
            if info:
                targets.append({"pos": (x, y), "item": info[0], "units": info[1], "bonus": info[2], "mls": info[3]})
            if isinstance(t, dict) and t.get("animal") and t.get("fertilizer_available"):
                targets.append({"pos": (x, y), "item": "FERTILIZER", "units": 1, "bonus": 0, "mls": -1})
    shed_tiles = _fd_shed_tiles(board)
    farmer_pos = tuple(farm["farmer"])
    money = float(farm.get("money", 0))
    already = len(farm.get("hands") or [])

    def build(n_hands):
        units = [{"pos": farmer_pos, "t": now, "tour": []}]
        occ = {p: 0 for p in shed_tiles}
        if farmer_pos in occ:
            occ[farmer_pos] += 1
        for _ in range(n_hands):
            b = sorted(occ.items(), key=lambda kv: (kv[1], shed_tiles.index(kv[0])))[0][0]
            occ[b] += 1
            units.append({"pos": b, "t": now + 1, "tour": []})
        remaining = list(range(len(targets)))
        total = 0.0
        while remaining:
            best = None
            for ui, u in enumerate(units):
                for ti in remaining:
                    tg = targets[ti]
                    d = _fd_dist(u["pos"], tg["pos"])
                    water = 1 if tg["bonus"] > 0 else 0
                    t_h = u["t"] + d + water
                    back = min(_fd_dist(tg["pos"], s) for s in shed_tiles)
                    slack = 4 if tg["item"] in _FD_HOLD else 2
                    if t_h + 1 + back > _FD_LAST - slack:   # premium goods reach the shed earlier
                        continue
                    got = _fd_units_at(tg["units"], tg["mls"], now, t_h) + (tg["bonus"] if water else 0)
                    if got <= 0:
                        continue
                    val = got * max(1, prices.get(tg["item"], 1))
                    score = val / (d + water + 1)
                    if best is None or score > best[0]:
                        best = (score, ui, ti, t_h, val)
            if best is None:
                break
            _, ui, ti, t_h, val = best
            u = units[ui]
            u["tour"].append(targets[ti]["pos"])
            u["pos"] = targets[ti]["pos"]
            u["t"] = t_h + 1
            total += val
            remaining.remove(ti)
        cost = sum(_fd_fib(already + i) for i in range(n_hands))
        return (total - cost, n_hands, [u["tour"] for u in units], total, cost)

    best = None
    for n in range(0, 15):
        if sum(_fd_fib(already + i) for i in range(n)) > money * 0.5:
            break
        res = build(n)
        if best is None or res[0] > best[0] + 1e-9:
            best = res
    tours = best[2]
    n = best[1]
    while n > 0 and not tours[n]:
        n -= 1
    return {"n_hands": n, "tours": tours[: n + 1]}


def _fd_unit_action(pos, inv, tour, step, day, shed_tiles, tiles, dropping):
    remaining = _FD_LAST - step
    carried = sum(int(v) for v in (inv or {}).values())
    home = min(shed_tiles, key=lambda p: (_fd_dist(pos, p), shed_tiles.index(p)))
    for tp in tour:
        t = tiles[tp[1]][tp[0]]
        info = _fd_tile_info(t, day)
        fert = isinstance(t, dict) and bool(t.get("animal")) and bool(t.get("fertilizer_available"))
        if not info and not fert:
            continue
        d = _fd_dist(pos, tp)
        work = 2 if (info and info[2] > 0) else 1
        back = min(_fd_dist(tp, s) for s in shed_tiles)
        if d + work + back > remaining:
            continue
        if d > 0:
            return [_fd_step_toward(pos, tp)]
        if info and info[2] > 0:
            return ["WATER"]
        if info:
            return ["HARVEST"]
        return ["COLLECT_FERTILIZER"]
    if carried > 0:
        if pos in shed_tiles:
            if dropping["load"] + carried <= dropping["room"] or remaining <= 0:
                dropping["load"] += carried
                return ["DROP"]
            return ["PASS"]
        return [_fd_step_toward(pos, home)]
    return ["PASS"]


def _fd_track_rival(obs, st):
    """Infer which rival units carry which goods from public tile/position changes."""
    seat = int(obs["player"])
    rival = obs["farms"][1 - seat]
    tiles = rival.get("tiles") or []
    board = len(tiles)
    shed_tiles = _fd_shed_tiles(board)
    positions = [tuple(rival["farmer"])] + [tuple(p) for p in (rival.get("hands") or [])]
    prev = st.get("rival_tiles")
    carry = st.setdefault("rival_carry", {})
    # units standing on the shed at the previous observation have dropped since
    for i, p in list(st.get("rival_pos_prev", {}).items()):
        if p in shed_tiles:
            carry.pop(i, None)
    if prev is not None:
        for y, row in enumerate(tiles):
            for x, t in enumerate(row):
                item0, u0 = _fd_tile_units(prev[y][x])
                item1, u1 = _fd_tile_units(t)
                if item0 and u0 > 0 and (item1 != item0 or u1 < u0):
                    took = u0 - (u1 if item1 == item0 else 0)
                    if took <= 0:
                        continue
                    for i, p in enumerate(positions):
                        if p == (x, y):
                            c = carry.setdefault(i, {})
                            c[item0] = c.get(item0, 0) + took
                            break
    st["rival_tiles"] = [list(r) for r in tiles]
    st["rival_pos_prev"] = {i: p for i, p in enumerate(positions)}
    threat = {}
    for i, goods in carry.items():
        if i >= len(positions):
            continue
        d = min(_fd_dist(positions[i], s) for s in shed_tiles)
        for item, q in goods.items():
            if q > 0:
                threat[item] = min(threat.get(item, 99), d)
    return threat


def _fd_act(obs):
    step = int(obs["step"])
    seat = int(obs["player"])
    st = _FD_STATE.get(seat)
    if st is None or st.get("game_step", 10 ** 9) > step:
        st = None
    if st is None:
        st = {"plan": _fd_plan(obs)}
        _FD_STATE[seat] = st
        _FD_REPORT["plans"] += 1
    st["game_step"] = step
    plan = st["plan"]
    farm = obs["farms"][seat]
    tiles = farm["tiles"]
    board = len(tiles)
    day = int(obs["day"])
    shed_tiles = _fd_shed_tiles(board)
    private = obs["private"]
    invs = private.get("inventories") or []
    shed = {k: int(v) for k, v in (private.get("shed") or {}).items()}
    room = 100 - sum(shed.values())
    dropping = {"load": 0, "room": max(0, room)}
    positions = [tuple(farm["farmer"])] + [tuple(p) for p in (farm.get("hands") or [])]
    acts = []
    for i, pos in enumerate(positions):
        tour = plan["tours"][i] if i < len(plan["tours"]) else []
        inv = invs[i] if i < len(invs) else {}
        acts.append(_fd_unit_action(pos, inv, tour, step, day, shed_tiles, tiles, dropping))
    for i, a in enumerate(acts):
        if a and a[0] == "DROP" and i < len(invs):
            for item, q in (invs[i] or {}).items():
                shed[item] = shed.get(item, 0) + int(q)
    threat = _fd_track_rival(obs, st)
    prices = {k: int(v) for k, v in (obs["market"]["prices"] or {}).items()}
    held = sum(q for item, q in shed.items() if item in _FD_HOLD)
    incoming = sum(int(v) for inv in invs for v in (inv or {}).values())
    # what a route-2 chassis in our seat would sell now, in its slot order: the best available
    # forecast of a mirror rival's queue this turn
    parent_order = []
    try:
        pact = _FD_PARENT(obs, None)
        for o in (pact.get("market") or []):
            if isinstance(o, list) and len(o) >= 3 and o[0] == "SELL" and o[1] not in parent_order:
                parent_order.append(o[1])
    except Exception:
        parent_order = []
    sells = []
    for item in _FD_ITEMS:
        q = int(shed.get(item, 0) or 0)
        if q <= 0:
            continue
        if item in _FD_HOLD and step < _FD_FLUSH:
            danger = threat.get(item, 99) <= 1 or item in parent_order
            crowded = held + incoming > 90
            if not danger and not crowded:
                continue
            if danger:
                _FD_REPORT["fronts"] += 1
        rank = parent_order.index(item) if item in parent_order else 100
        sells.append((rank, -q * max(1, prices.get(item, 1)), item))
    sells.sort()
    market = [["SELL", item, 999] for _, _, item in sells]
    hires_wanted = max(0, plan["n_hands"] - len(positions) + 1)
    if hires_wanted and step == _FD_START:
        keep = max(0, 10 - hires_wanted)
        market = market[:keep] + [["HIRE"] for _ in range(min(10, hires_wanted))]
        _FD_REPORT["hires"] += min(10, hires_wanted)
    return {"farmer": acts[0], "hands": acts[1:], "market": market[:10]}


_FD_PARENT = agent
def agent(observation, configuration=None):
    try:
        step = int(observation["step"])
    except Exception:
        return _FD_PARENT(observation, configuration)
    if step < _FD_START:
        return _FD_PARENT(observation, configuration)
    try:
        return _fd_act(observation)
    except Exception:
        _FD_REPORT["errors"] += 1
        return _FD_PARENT(observation, configuration)
agent = globals().pop("agent")
globals().pop("kaggle_submission_agent", None)
kaggle_submission_agent = agent
